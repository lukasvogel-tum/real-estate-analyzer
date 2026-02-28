import os
from typing import Iterable

import lancedb
from langchain_community.vectorstores import LanceDB
from langchain_core.documents import Document

from utils.embeddings import get_embeddings

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "lancedb")
REALESTATE_GLOBAL_TABLE = "realestate_global"


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


def get_vectorstore(project_name: str):
    """Laedt einen existierenden VectorStore fuer ein Projekt."""
    return _get_vectorstore_for_table(get_table_name(project_name))


def get_realestate_global_vectorstore():
    """Laedt den globalen Immobilien-Index (shared table)."""
    return _get_vectorstore_for_table(REALESTATE_GLOBAL_TABLE)


def _with_project_metadata(
    documents: Iterable[Document], project_name: str, project_type: str | None
) -> list[Document]:
    normalized_project_name = (project_name or "").strip()
    normalized_project_type = (project_type or "").strip().lower() if project_type else None
    enriched_documents = []

    for doc in documents:
        metadata = dict(doc.metadata or {})
        metadata.setdefault("source", "Unbekannt")
        if normalized_project_name:
            metadata["project_name"] = normalized_project_name
        if normalized_project_type:
            metadata["project_type"] = normalized_project_type
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


def add_documents_to_project(
    project_name: str, documents: list[Document], project_type: str | None = None
):
    """Fuegt Dokumente ins Projekt ein und spiegelt sie in den RealEstate-Global-Index."""
    db = _connect_db()
    embeddings = get_embeddings()
    table_name = get_table_name(project_name)
    enriched_documents = _with_project_metadata(documents, project_name, project_type)

    _upsert_documents_in_table(db, table_name, embeddings, enriched_documents)
    _upsert_documents_in_table(db, REALESTATE_GLOBAL_TABLE, embeddings, enriched_documents)
