import re

from services.graph_db import execute_cypher, graph_is_enabled
from services.graph_ingest import build_scope_key


STOP_WORDS = {
    "und",
    "oder",
    "aber",
    "eine",
    "einer",
    "eines",
    "einem",
    "einen",
    "der",
    "die",
    "das",
    "dem",
    "den",
    "des",
    "mit",
    "ohne",
    "über",
    "fuer",
    "für",
    "from",
    "what",
    "which",
    "where",
    "when",
    "how",
    "have",
    "this",
    "that",
    "into",
    "does",
    "tell",
    "show",
    "about",
}


def _extract_query_terms(query: str) -> list[str]:
    phrases = [match.group(1).strip().lower() for match in re.finditer(r'"([^"]+)"', query or "")]
    words = []
    for raw in re.findall(r"[A-Za-zÀ-ÿ0-9_-]{4,}", query or ""):
        cleaned = raw.strip().lower()
        if cleaned in STOP_WORDS:
            continue
        if cleaned not in words:
            words.append(cleaned)

    terms = []
    for term in phrases + words:
        if term and term not in terms:
            terms.append(term)
    return terms[:10]


def _scope_where_clause(scope: str, project_name: str | None) -> tuple[str, dict]:
    normalized_scope = (scope or "global").strip().lower()
    if normalized_scope == "project" and project_name:
        scope_key = build_scope_key("project", project_name)
        return "s.scope_key = $scope_key", {"scope_key": scope_key}

    if normalized_scope == "realestate_global":
        return "s.scope_type = 'project'", {}

    return "1 = 1", {}


def get_graph_context_for_chat(
    *,
    query: str,
    scope: str,
    project_name: str | None = None,
    max_entities: int = 8,
    max_relationships: int = 8,
) -> dict:
    if not graph_is_enabled():
        return {"graph_context": "", "graph_facts": []}

    terms = _extract_query_terms(query)
    if not terms:
        return {"graph_context": "", "graph_facts": []}

    scope_clause, scope_params = _scope_where_clause(scope, project_name)
    entity_rows = execute_cypher(
        f"""
        MATCH (e:Entity)-[:MENTIONED_IN]->(c:Chunk)-[:IN_SCOPE]->(s:Scope)
        WHERE ({scope_clause})
          AND ANY(term IN $terms WHERE
            toLower(coalesce(e.name, '')) CONTAINS term OR
            ANY(alias IN coalesce(e.aliases, []) WHERE toLower(alias) CONTAINS term)
          )
        RETURN e.entity_key AS entity_key,
               e.name AS name,
               e.entity_type AS entity_type,
               e.description AS description,
               count(DISTINCT c.chunk_id) AS mention_count,
               collect(DISTINCT c.source)[0..3] AS sources
        ORDER BY mention_count DESC, name ASC
        LIMIT $max_entities
        """,
        {
            **scope_params,
            "terms": terms,
            "max_entities": max_entities,
        },
    )

    if not entity_rows:
        return {"graph_context": "", "graph_facts": []}

    entity_keys = [row["entity_key"] for row in entity_rows if row.get("entity_key")]
    relationship_rows = execute_cypher(
        f"""
        MATCH (source:Entity)-[r:RELATES_TO]->(target:Entity)
        MATCH (source)-[:IN_SCOPE]->(s:Scope)
        WHERE ({scope_clause})
          AND source.entity_key IN $entity_keys
        RETURN source.name AS source_name,
               source.entity_type AS source_type,
               r.relation_type AS relation_type,
               target.name AS target_name,
               target.entity_type AS target_type,
               r.description AS description,
               r.confidence AS confidence
        ORDER BY coalesce(r.confidence, 0.0) DESC, source_name ASC
        LIMIT $max_relationships
        """,
        {
            **scope_params,
            "entity_keys": entity_keys,
            "max_relationships": max_relationships,
        },
    )

    graph_facts = []
    context_lines = []

    for row in entity_rows:
        sources = [source for source in row.get("sources", []) if source]
        fact_text = (
            f"Entity: {row.get('name')} ({row.get('entity_type')}) "
            f"mentioned in {int(row.get('mention_count') or 0)} chunks"
        )
        if sources:
            fact_text += f" from {', '.join(sources)}"
        if row.get("description"):
            fact_text += f". Note: {row['description']}"

        graph_facts.append(
            {
                "kind": "entity",
                "label": row.get("name"),
                "text": fact_text,
            }
        )
        context_lines.append(fact_text)

    for row in relationship_rows:
        relation_text = (
            f"Relation: {row.get('source_name')} ({row.get('source_type')}) "
            f"-[{row.get('relation_type')}]-> {row.get('target_name')} ({row.get('target_type')})"
        )
        if row.get("description"):
            relation_text += f". Note: {row['description']}"

        graph_facts.append(
            {
                "kind": "relationship",
                "label": row.get("relation_type"),
                "text": relation_text,
            }
        )
        context_lines.append(relation_text)

    return {
        "graph_context": "\n".join(context_lines),
        "graph_facts": graph_facts,
    }
