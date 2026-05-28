import os
import re

from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI


DEFAULT_GRAPH_MODEL = "gpt-4o-mini"
GRAPH_ENTITY_EXTRACTION_ENABLED = os.getenv(
    "GRAPH_ENTITY_EXTRACTION_ENABLED", "true"
).strip().lower() in {"1", "true", "yes", "on"}


def _safe_max_chunks() -> int:
    raw_value = (os.getenv("GRAPH_ENTITY_EXTRACTION_MAX_CHUNKS", "8") or "8").strip()
    try:
        return max(0, int(raw_value))
    except ValueError:
        return 8


GRAPH_ENTITY_EXTRACTION_MAX_CHUNKS = _safe_max_chunks()

ALLOWED_ENTITY_TYPES = {
    "property",
    "person",
    "company",
    "loan",
    "bank",
    "account",
    "insurance_policy",
    "contract",
    "location",
    "project",
    "organization",
    "tenant",
    "advisor",
}


class ExtractedEntity(BaseModel):
    entity_type: str = Field(description="Entity type from the allowed list.")
    name: str = Field(description="Canonical display name of the entity.")
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    confidence: float | None = None


class ExtractedRelationship(BaseModel):
    source_name: str
    source_type: str | None = None
    relation_type: str = Field(description="Short snake_case relationship type.")
    target_name: str
    target_type: str | None = None
    description: str | None = None
    confidence: float | None = None


class GraphExtractionResult(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relationships: list[ExtractedRelationship] = Field(default_factory=list)


def _normalize_entity_type(entity_type: str | None) -> str:
    normalized = re.sub(r"[^a-z_]+", "_", (entity_type or "").strip().lower()).strip("_")
    if normalized in ALLOWED_ENTITY_TYPES:
        return normalized
    return "organization"


def _clean_name(name: str | None) -> str:
    cleaned = re.sub(r"\s+", " ", (name or "").strip())
    return cleaned[:200]


def _deduplicate_entities(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    deduped: dict[tuple[str, str], ExtractedEntity] = {}
    for entity in entities:
        normalized_type = _normalize_entity_type(entity.entity_type)
        cleaned_name = _clean_name(entity.name)
        if not cleaned_name:
            continue

        key = (normalized_type, cleaned_name.lower())
        aliases = []
        seen_aliases = set()
        for alias in entity.aliases:
            cleaned_alias = _clean_name(alias)
            if not cleaned_alias:
                continue
            lowered = cleaned_alias.lower()
            if lowered in seen_aliases or lowered == cleaned_name.lower():
                continue
            seen_aliases.add(lowered)
            aliases.append(cleaned_alias)

        normalized_entity = ExtractedEntity(
            entity_type=normalized_type,
            name=cleaned_name,
            aliases=aliases,
            description=(entity.description or "").strip() or None,
            confidence=entity.confidence,
        )

        existing = deduped.get(key)
        if existing is None:
            deduped[key] = normalized_entity
            continue

        existing_aliases = set(alias.lower() for alias in existing.aliases)
        merged_aliases = existing.aliases + [
            alias for alias in normalized_entity.aliases if alias.lower() not in existing_aliases
        ]
        deduped[key] = ExtractedEntity(
            entity_type=existing.entity_type,
            name=existing.name,
            aliases=merged_aliases,
            description=existing.description or normalized_entity.description,
            confidence=max(
                [value for value in [existing.confidence, normalized_entity.confidence] if value is not None],
                default=None,
            ),
        )

    return list(deduped.values())


def _deduplicate_relationships(
    relationships: list[ExtractedRelationship],
) -> list[ExtractedRelationship]:
    deduped: dict[tuple[str, str, str], ExtractedRelationship] = {}

    for relationship in relationships:
        source_name = _clean_name(relationship.source_name)
        target_name = _clean_name(relationship.target_name)
        relation_type = re.sub(
            r"[^a-z_]+", "_", (relationship.relation_type or "").strip().lower()
        ).strip("_")
        if not source_name or not target_name or not relation_type:
            continue

        normalized_relationship = ExtractedRelationship(
            source_name=source_name,
            source_type=_normalize_entity_type(relationship.source_type),
            relation_type=relation_type,
            target_name=target_name,
            target_type=_normalize_entity_type(relationship.target_type),
            description=(relationship.description or "").strip() or None,
            confidence=relationship.confidence,
        )
        key = (source_name.lower(), relation_type, target_name.lower())
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = normalized_relationship
            continue

        deduped[key] = ExtractedRelationship(
            source_name=existing.source_name,
            source_type=existing.source_type or normalized_relationship.source_type,
            relation_type=existing.relation_type,
            target_name=existing.target_name,
            target_type=existing.target_type or normalized_relationship.target_type,
            description=existing.description or normalized_relationship.description,
            confidence=max(
                [value for value in [existing.confidence, normalized_relationship.confidence] if value is not None],
                default=None,
            ),
        )

    return list(deduped.values())


def _fallback_entities(metadata: dict) -> GraphExtractionResult:
    project_name = _clean_name(metadata.get("project_name"))
    scope_type = (metadata.get("scope_type") or "").strip().lower()
    if scope_type == "project" and project_name:
        return GraphExtractionResult(
            entities=[
                ExtractedEntity(
                    entity_type="project",
                    name=project_name,
                    aliases=[],
                    description="Project workspace inferred from upload metadata.",
                    confidence=0.6,
                )
            ]
        )
    return GraphExtractionResult()


def extract_graph_knowledge(text: str, metadata: dict | None = None) -> GraphExtractionResult:
    metadata = dict(metadata or {})
    if not GRAPH_ENTITY_EXTRACTION_ENABLED:
        return _fallback_entities(metadata)

    cleaned_text = (text or "").strip()
    if not cleaned_text:
        return _fallback_entities(metadata)

    if not os.getenv("OPENAI_API_KEY"):
        return _fallback_entities(metadata)

    system_prompt = (
        "You extract explicit family-office and real-estate knowledge from a document chunk. "
        "Return only entities and relationships that are directly supported by the text. "
        "Allowed entity types: property, person, company, loan, bank, account, "
        "insurance_policy, contract, location, project, organization, tenant, advisor. "
        "Use short snake_case relation types like owns, located_in, finances, managed_by, "
        "leased_to, guarantees, associated_with, mentions. "
        "Do not invent entities or infer legal conclusions. Be conservative."
    )

    user_prompt = (
        f"Metadata:\n{metadata}\n\n"
        f"Chunk text:\n{cleaned_text[:6000]}"
    )

    try:
        llm = ChatOpenAI(model_name=DEFAULT_GRAPH_MODEL, temperature=0)
        structured_llm = llm.with_structured_output(GraphExtractionResult)
        result = structured_llm.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
    except Exception:
        return _fallback_entities(metadata)

    deduped_entities = _deduplicate_entities(result.entities)
    deduped_relationships = _deduplicate_relationships(result.relationships)
    fallback = _fallback_entities(metadata)

    return GraphExtractionResult(
        entities=_deduplicate_entities(deduped_entities + fallback.entities),
        relationships=deduped_relationships,
    )
