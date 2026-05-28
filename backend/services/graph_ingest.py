from collections import defaultdict
from datetime import datetime, timezone
import re

from langchain_core.documents import Document

from services.graph_db import get_graph_database, get_graph_driver, graph_is_enabled
from services.graph_extraction import (
    GRAPH_ENTITY_EXTRACTION_MAX_CHUNKS,
    GraphExtractionResult,
    extract_graph_knowledge,
)


def build_scope_key(scope_type: str, scope_id: str) -> str:
    return f"{(scope_type or 'project').strip().lower()}:{(scope_id or '').strip()}"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_name(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())[:200]


def _normalize_entity_type(value: str | None) -> str:
    normalized = re.sub(r"[^a-z_]+", "_", (value or "").strip().lower()).strip("_")
    return normalized or "organization"


def _entity_key(scope_key: str, entity_type: str, name: str) -> str:
    normalized_name = re.sub(r"[^a-z0-9]+", "_", name.strip().lower()).strip("_")
    normalized_type = _normalize_entity_type(entity_type)
    return f"{scope_key}::{normalized_type}::{normalized_name}"


def _group_chunks_by_source(documents: list[Document]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for index, document in enumerate(documents):
        metadata = document.metadata or {}
        source = str(metadata.get("source", "unknown")).strip() or "unknown"
        chunk_id = metadata.get("chunk_id") or f"{source}::chunk::{index}"
        grouped[source].append(
            {
                "chunk_id": chunk_id,
                "chunk_index": index,
                "content": document.page_content,
                "source": source,
                "scope_type": metadata.get("scope_type"),
                "scope_id": metadata.get("scope_id"),
                "document_type": metadata.get("document_type"),
                "project_name": metadata.get("project_name"),
                "project_type": metadata.get("project_type"),
            }
        )

    return grouped


def _prepare_graph_knowledge(
    scope_key: str,
    chunk: dict,
    extraction: GraphExtractionResult,
) -> tuple[list[dict], list[dict]]:
    entities_by_key: dict[tuple[str, str], dict] = {}
    prepared_relationships: list[dict] = []

    for entity in extraction.entities:
        entity_type = _normalize_entity_type(entity.entity_type)
        name = _normalize_name(entity.name)
        if not name:
            continue

        key = (entity_type, name.lower())
        entity_key = _entity_key(scope_key, entity_type, name)
        aliases = []
        seen_aliases = set()
        for alias in entity.aliases:
            cleaned_alias = _normalize_name(alias)
            if not cleaned_alias:
                continue
            lowered = cleaned_alias.lower()
            if lowered == name.lower() or lowered in seen_aliases:
                continue
            seen_aliases.add(lowered)
            aliases.append(cleaned_alias)

        entities_by_key[key] = {
            "entity_key": entity_key,
            "entity_type": entity_type,
            "name": name,
            "normalized_name": name.lower(),
            "aliases": aliases,
            "description": (entity.description or "").strip() or None,
            "confidence": entity.confidence,
            "scope_key": scope_key,
            "chunk_id": chunk["chunk_id"],
            "source": chunk.get("source"),
        }

    for relationship in extraction.relationships:
        source_name = _normalize_name(relationship.source_name)
        target_name = _normalize_name(relationship.target_name)
        relation_type = re.sub(
            r"[^a-z_]+", "_", (relationship.relation_type or "").strip().lower()
        ).strip("_")
        if not source_name or not target_name or not relation_type:
            continue

        source_type = _normalize_entity_type(relationship.source_type)
        target_type = _normalize_entity_type(relationship.target_type)
        source_key = (source_type, source_name.lower())
        target_key = (target_type, target_name.lower())
        if source_key not in entities_by_key:
            entities_by_key[source_key] = {
                "entity_key": _entity_key(scope_key, source_type, source_name),
                "entity_type": source_type,
                "name": source_name,
                "normalized_name": source_name.lower(),
                "aliases": [],
                "description": None,
                "confidence": relationship.confidence,
                "scope_key": scope_key,
                "chunk_id": chunk["chunk_id"],
                "source": chunk.get("source"),
            }
        if target_key not in entities_by_key:
            entities_by_key[target_key] = {
                "entity_key": _entity_key(scope_key, target_type, target_name),
                "entity_type": target_type,
                "name": target_name,
                "normalized_name": target_name.lower(),
                "aliases": [],
                "description": None,
                "confidence": relationship.confidence,
                "scope_key": scope_key,
                "chunk_id": chunk["chunk_id"],
                "source": chunk.get("source"),
            }

        prepared_relationships.append(
            {
                "source_entity_key": entities_by_key[source_key]["entity_key"],
                "target_entity_key": entities_by_key[target_key]["entity_key"],
                "relation_type": relation_type,
                "description": (relationship.description or "").strip() or None,
                "confidence": relationship.confidence,
                "scope_key": scope_key,
                "source_chunk_id": chunk["chunk_id"],
            }
        )

    return list(entities_by_key.values()), prepared_relationships


def _upsert_chunk_knowledge(session, scope_key: str, chunk: dict, now_iso: str) -> tuple[int, int]:
    extraction = extract_graph_knowledge(chunk.get("content", ""), metadata=chunk)
    entities, relationships = _prepare_graph_knowledge(scope_key, chunk, extraction)

    if entities:
        session.run(
            """
            MATCH (c:Chunk {chunk_id: $chunk_id})
            MATCH (s:Scope {scope_key: $scope_key})
            UNWIND $entities AS entity
            MERGE (e:Entity {entity_key: entity.entity_key})
            SET e.entity_type = entity.entity_type,
                e.name = entity.name,
                e.normalized_name = entity.normalized_name,
                e.aliases = entity.aliases,
                e.description = entity.description,
                e.updated_at = $now_iso
            ON CREATE SET e.created_at = $now_iso
            MERGE (e)-[:IN_SCOPE]->(s)
            MERGE (e)-[m:MENTIONED_IN {chunk_id: $chunk_id}]->(c)
            SET m.confidence = entity.confidence,
                m.source = entity.source,
                m.updated_at = $now_iso
            """,
            {
                "chunk_id": chunk["chunk_id"],
                "scope_key": scope_key,
                "entities": entities,
                "now_iso": now_iso,
            },
        )

    if relationships:
        session.run(
            """
            UNWIND $relationships AS rel
            MATCH (source:Entity {entity_key: rel.source_entity_key})
            MATCH (target:Entity {entity_key: rel.target_entity_key})
            MERGE (source)-[r:RELATES_TO {
              relation_type: rel.relation_type,
              source_chunk_id: rel.source_chunk_id,
              target_entity_key: rel.target_entity_key
            }]->(target)
            SET r.description = rel.description,
                r.confidence = rel.confidence,
                r.scope_key = rel.scope_key,
                r.updated_at = $now_iso
            ON CREATE SET r.created_at = $now_iso
            """,
            {
                "relationships": relationships,
                "now_iso": now_iso,
            },
        )

    return len(entities), len(relationships)


def ingest_upload_to_graph(
    *,
    project_name: str,
    project_type: str | None,
    scope_type: str,
    scope_id: str,
    document_type: str,
    uploaded_file_records: list[dict],
    documents: list[Document],
) -> dict[str, str | int]:
    if not graph_is_enabled():
        return {"status": "disabled", "documents_indexed": 0}

    driver = get_graph_driver()
    if driver is None:
        return {"status": "disabled", "documents_indexed": 0}

    scope_key = build_scope_key(scope_type, scope_id)
    now_iso = _utc_now_iso()
    chunks_by_source = _group_chunks_by_source(documents)

    graph_document_count = 0
    extracted_chunk_count = 0
    entity_count = 0
    relationship_count = 0

    with driver.session(database=get_graph_database()) as session:
        for record in uploaded_file_records:
            source_filename = record["source_filename"]
            stored_file_path = record["stored_file_path"]
            stored_text_path = record["stored_text_path"]
            file_size_bytes = record.get("file_size_bytes")
            document_key = f"{scope_key}::{source_filename}"
            document_chunks = chunks_by_source.get(source_filename, [])

            session.run(
                """
                MERGE (s:Scope {scope_key: $scope_key})
                SET s.scope_type = $scope_type,
                    s.scope_id = $scope_id,
                    s.updated_at = $now_iso
                WITH s
                FOREACH (_ IN CASE WHEN $scope_type = 'project' THEN [1] ELSE [] END |
                  MERGE (p:Project {project_name: $project_name})
                  SET p.project_type = $project_type,
                      p.scope_key = $scope_key,
                      p.updated_at = $now_iso
                  MERGE (p)-[:IN_SCOPE]->(s)
                )
                MERGE (d:Document {document_key: $document_key})
                SET d.source_filename = $source_filename,
                    d.project_name = $project_name,
                    d.project_type = $project_type,
                    d.scope_type = $scope_type,
                    d.scope_id = $scope_id,
                    d.scope_key = $scope_key,
                    d.document_type = $document_type,
                    d.stored_file_path = $stored_file_path,
                    d.stored_text_path = $stored_text_path,
                    d.file_size_bytes = $file_size_bytes,
                    d.updated_at = $now_iso
                ON CREATE SET d.created_at = $now_iso
                MERGE (d)-[:IN_SCOPE]->(s)
                WITH d, s
                FOREACH (_ IN CASE WHEN $scope_type = 'project' THEN [1] ELSE [] END |
                  MERGE (p:Project {project_name: $project_name})
                  MERGE (d)-[:BELONGS_TO_PROJECT]->(p)
                )
                WITH d, s
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(existing:Chunk)
                DETACH DELETE existing
                WITH d, s
                UNWIND $chunks AS chunk
                CREATE (c:Chunk {
                  chunk_id: chunk.chunk_id,
                  chunk_index: chunk.chunk_index,
                  content: chunk.content,
                  source: chunk.source,
                  scope_type: chunk.scope_type,
                  scope_id: chunk.scope_id,
                  document_type: chunk.document_type,
                  project_name: chunk.project_name,
                  project_type: chunk.project_type,
                  document_key: $document_key,
                  updated_at: $now_iso,
                  created_at: $now_iso
                })
                MERGE (d)-[:HAS_CHUNK]->(c)
                MERGE (c)-[:IN_SCOPE]->(s)
                """,
                {
                    "scope_key": scope_key,
                    "scope_type": scope_type,
                    "scope_id": scope_id,
                    "project_name": project_name,
                    "project_type": project_type,
                    "document_key": document_key,
                    "source_filename": source_filename,
                    "document_type": document_type,
                    "stored_file_path": stored_file_path,
                    "stored_text_path": stored_text_path,
                    "file_size_bytes": file_size_bytes,
                    "chunks": document_chunks,
                    "now_iso": now_iso,
                },
            )

            remaining_chunk_budget = max(
                0, GRAPH_ENTITY_EXTRACTION_MAX_CHUNKS - extracted_chunk_count
            )
            if remaining_chunk_budget > 0:
                for chunk in document_chunks[:remaining_chunk_budget]:
                    chunk_entities, chunk_relationships = _upsert_chunk_knowledge(
                        session, scope_key, chunk, now_iso
                    )
                    extracted_chunk_count += 1
                    entity_count += chunk_entities
                    relationship_count += chunk_relationships

            graph_document_count += 1

    return {
        "status": "indexed",
        "documents_indexed": graph_document_count,
        "chunks_extracted": extracted_chunk_count,
        "entities_indexed": entity_count,
        "relationships_indexed": relationship_count,
    }
