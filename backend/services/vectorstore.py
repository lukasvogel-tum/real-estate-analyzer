import os
from typing import Iterable

import lancedb
from langchain_community.vectorstores import LanceDB
from langchain_core.documents import Document

from utils.embeddings import get_embeddings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "lancedb")
REALESTATE_GLOBAL_TABLE = "realestate_global"
GLOBAL_BRAIN_TABLE = "global_brain"


def get_table_name(project_name: str) -> str:
    """Erzeugt einen sicheren Tabellennamen aus dem Projektnamen."""
    return project_name.lower().replace(" ", "_")


def _connect_db():
    return lancedb.connect(DB_PATH)


def _get_table_names(db) -> set[str]:
    try:
        return set(db.table_names())
    except Exception:
        return set()


def _get_vectorstore_for_table(table_name: str):
    db = _connect_db()
    embeddings = get_embeddings()

    if table_name in _get_table_names(db):
        return LanceDB(connection=db, embedding=embeddings, table_name=table_name)
    return None


def has_vectorstore_table(table_name: str) -> bool:
    """Return table availability without initializing embeddings."""
    db = _connect_db()
    return table_name in _get_table_names(db)


def has_realestate_global_vectorstore() -> bool:
    """Check whether the shared real-estate table exists."""
    return has_vectorstore_table(REALESTATE_GLOBAL_TABLE)


def has_global_brain_vectorstore() -> bool:
    """Check whether the shared global brain table exists."""
    return has_vectorstore_table(GLOBAL_BRAIN_TABLE)


def get_vectorstore(project_name: str):
    """Laedt einen existierenden VectorStore fuer ein Projekt."""
    return _get_vectorstore_for_table(get_table_name(project_name))


def get_realestate_global_vectorstore():
    """Laedt den globalen Immobilien-Index (shared table)."""
    return _get_vectorstore_for_table(REALESTATE_GLOBAL_TABLE)


def get_global_brain_vectorstore():
    """Laedt den globalen Brain-Index (shared table ueber alle Domains)."""
    return _get_vectorstore_for_table(GLOBAL_BRAIN_TABLE)


def _with_document_metadata(
    documents: Iterable[Document],
    project_name: str,
    project_type: str | None,
    scope_type: str,
    scope_id: str,
    document_type: str,
) -> list[Document]:
    normalized_project_name = (project_name or "").strip()
    normalized_project_type = (project_type or "").strip().lower() if project_type else None
    normalized_scope_type = (scope_type or "").strip().lower()
    normalized_scope_id = (scope_id or "").strip()
    normalized_document_type = (document_type or "").strip().lower() or "general"
    enriched_documents = []

    for doc in documents:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("source", "Unbekannt")
        if normalized_project_name:
            metadata["project_name"] = normalized_project_name
        if normalized_project_type:
            metadata["project_type"] = normalized_project_type
        if normalized_scope_type:
            metadata["scope_type"] = normalized_scope_type
        if normalized_scope_id:
            metadata["scope_id"] = normalized_scope_id
        metadata["document_type"] = normalized_document_type
        enriched_documents.append(Document(page_content=doc.page_content, metadata=metadata))

    return enriched_documents


def _upsert_documents_in_table(db, table_name: str, embeddings, documents: list[Document]):
    if not documents:
        return

    if table_name in _get_table_names(db):
        vectorstore = LanceDB(connection=db, embedding=embeddings, table_name=table_name)
        try:
            vectorstore.add_documents(documents)
        except ValueError as exc:
            if "not found in target schema" in str(exc):
                db.drop_table(table_name)
                LanceDB.from_documents(
                    documents, embeddings, connection=db, table_name=table_name
                )
            else:
                raise exc
    else:
        LanceDB.from_documents(documents, embeddings, connection=db, table_name=table_name)


def add_documents_to_scope(
    scope_type: str,
    scope_id: str,
    documents: list[Document],
    project_name: str,
    project_type: str | None = None,
    document_type: str = "general",
):
    """Fuegt Dokumente in den passenden Scope-Index ein."""
    normalized_scope_type = (scope_type or "").strip().lower() or "project"
    normalized_scope_id = (scope_id or "").strip() or project_name

    db = _connect_db()
    embeddings = get_embeddings()
    enriched_documents = _with_document_metadata(
        documents,
        project_name=project_name,
        project_type=project_type,
        scope_type=normalized_scope_type,
        scope_id=normalized_scope_id,
        document_type=document_type,
    )

    if normalized_scope_type == "project":
        project_table_name = get_table_name(project_name)
        _upsert_documents_in_table(db, project_table_name, embeddings, enriched_documents)
        _upsert_documents_in_table(db, REALESTATE_GLOBAL_TABLE, embeddings, enriched_documents)

    _upsert_documents_in_table(db, GLOBAL_BRAIN_TABLE, embeddings, enriched_documents)


def add_documents_to_project(
    project_name: str,
    documents: list[Document],
    project_type: str | None = None,
    document_type: str = "general",
):
    """Backward-compatible wrapper fuer projektbezogenes Indexing."""
    add_documents_to_scope(
        scope_type="project",
        scope_id=project_name,
        documents=documents,
        project_name=project_name,
        project_type=project_type,
        document_type=document_type,
    )
