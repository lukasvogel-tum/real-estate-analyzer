from typing import Any

from services.project_registry import list_projects
from services.vectorstore import (
    get_global_brain_vectorstore,
    get_realestate_global_vectorstore,
    get_vectorstore,
)

VALID_SCOPES = {"project", "realestate_global", "global"}


def normalize_scope(scope: str | None) -> str:
    normalized = (scope or "project").strip().lower()
    if normalized not in VALID_SCOPES:
        valid = ", ".join(sorted(VALID_SCOPES))
        raise ValueError(f"Invalid scope '{scope}'. Allowed values: {valid}.")
    return normalized


def _similarity_search_with_scores(vectorstore, query: str, top_k: int):
    try:
        return vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
    except Exception:
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.invoke(query)
        return [(doc, None) for doc in docs]


def _fanout_realestate_search(query: str, top_k: int):
    candidates = []

    for project in list_projects():
        if not project.get("has_vector_index"):
            continue

        project_name = project.get("project_name")
        if not project_name:
            continue

        vectorstore = get_vectorstore(project_name)
        if vectorstore is None:
            continue

        project_hits = _similarity_search_with_scores(vectorstore, query, top_k)
        candidates.extend(project_hits)

    candidates.sort(key=lambda item: (item[1] is None, -(item[1] or 0.0)))
    return candidates[:top_k]


def resolve_chat_scope(scope: str | None, project_name: str | None, query: str, top_k: int) -> dict[str, Any]:
    normalized_scope = normalize_scope(scope)

    if normalized_scope == "project":
        cleaned_project_name = (project_name or "").strip()
        if not cleaned_project_name:
            raise ValueError("project_name is required when scope is 'project'.")

        project_vectorstore = get_vectorstore(cleaned_project_name)
        if project_vectorstore is None:
            raise LookupError(
                f"Project '{cleaned_project_name}' not found or has no indexed documents."
            )

        return {
            "mode": "vectorstore",
            "scope": normalized_scope,
            "effective_scope": normalized_scope,
            "vectorstore": project_vectorstore,
        }

    if normalized_scope == "realestate_global":
        shared_vectorstore = get_realestate_global_vectorstore()
        if shared_vectorstore is not None:
            return {
                "mode": "vectorstore",
                "scope": normalized_scope,
                "effective_scope": normalized_scope,
                "vectorstore": shared_vectorstore,
            }

        fallback_hits = _fanout_realestate_search(query, top_k)
        if not fallback_hits:
            raise LookupError("No indexed real estate documents found for the requested scope.")

        return {
            "mode": "documents",
            "scope": normalized_scope,
            "effective_scope": "realestate_global_fallback",
            "retrieved_documents": fallback_hits,
        }

    # Scope `global`: prefer the dedicated global brain table.
    global_vectorstore = get_global_brain_vectorstore()
    if global_vectorstore is not None:
        return {
            "mode": "vectorstore",
            "scope": normalized_scope,
            "effective_scope": normalized_scope,
            "vectorstore": global_vectorstore,
        }

    # Compatibility fallback for environments without `global_brain` table yet.
    shared_realestate = get_realestate_global_vectorstore()
    if shared_realestate is not None:
        return {
            "mode": "vectorstore",
            "scope": normalized_scope,
            "effective_scope": "global_fallback_realestate",
            "vectorstore": shared_realestate,
        }

    fallback_hits = _fanout_realestate_search(query, top_k)
    if not fallback_hits:
        raise LookupError("No indexed documents found for the requested global scope.")

    return {
        "mode": "documents",
        "scope": normalized_scope,
        "effective_scope": "global_fallback_realestate_project_fanout",
        "retrieved_documents": fallback_hits,
    }
