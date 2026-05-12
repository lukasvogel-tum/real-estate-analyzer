import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv()

from services.graph_db import close_graph_driver, init_graph
from services.graph_ingest import ingest_upload_to_graph
from services.graph_queries import get_graph_context_for_chat
from services.metadata_db import add_document_record, init_metadata_db
from services.project_registry import (
    get_project,
    list_projects,
    normalize_project_type,
    upsert_project,
)
from services.rag import (
    apply_metadata_filters,
    generate_answer,
    generate_answer_from_documents,
)
from services.scope_retriever import resolve_chat_scope
from services.system_status import get_knowledge_status
from services.vectorstore import add_documents_to_scope
from utils.extract_file import extract_text_from_file
from utils.text_splitter import split_text

app = FastAPI()
CORS_ALLOW_ORIGINS = os.getenv(
    "CORS_ALLOW_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000",
)
ALLOW_ORIGINS = [
    origin.strip() for origin in CORS_ALLOW_ORIGINS.split(",") if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_openai_key = os.getenv("OPENAI_API_KEY")
if _openai_key:
    os.environ["OPENAI_API_KEY"] = _openai_key
VALID_UPLOAD_SCOPE_TYPES = {"project", "domain", "global"}


def _normalize_upload_scope_type(scope_type: str | None) -> str:
    normalized = (scope_type or "project").strip().lower()
    if normalized not in VALID_UPLOAD_SCOPE_TYPES:
        valid = ", ".join(sorted(VALID_UPLOAD_SCOPE_TYPES))
        raise ValueError(f"Invalid scope_type '{scope_type}'. Allowed values: {valid}.")
    return normalized


def _resolve_scope_id(
    scope_type: str, scope_id: str | None, project_name: str | None
) -> str:
    cleaned_scope_id = (scope_id or "").strip()
    cleaned_project_name = (project_name or "").strip()

    if scope_type == "project":
        effective_scope_id = cleaned_scope_id or cleaned_project_name
        if not effective_scope_id:
            raise ValueError(
                "scope_id is required for scope_type 'project' (or provide project_name)."
            )
        return effective_scope_id

    if scope_type == "global":
        return cleaned_scope_id or "global"

    if not cleaned_scope_id:
        raise ValueError("scope_id is required for scope_type 'domain'.")
    return cleaned_scope_id


def _validate_storage_segment(value: str, label: str) -> str:
    cleaned = (value or "").strip()
    if not cleaned:
        raise ValueError(f"{label} is required.")
    if "/" in cleaned or "\\" in cleaned or cleaned in {".", ".."} or ".." in cleaned:
        raise ValueError(f"{label} contains invalid path characters.")
    return cleaned


def _normalize_document_type(document_type: str | None) -> str:
    normalized = (document_type or "general").strip().lower()
    return normalized or "general"


@app.on_event("startup")
def startup_event() -> None:
    init_metadata_db()
    init_graph()


@app.on_event("shutdown")
def shutdown_event() -> None:
    close_graph_driver()


@app.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    project_name: str | None = Form(default=None),
    project_type: str | None = Form(default=None),
    scope_type: str = Form(default="project"),
    scope_id: str | None = Form(default=None),
    document_type: str | None = Form(default=None),
):
    if not files or len(files) == 0:
        raise HTTPException(status_code=422, detail="No files provided.")

    try:
        normalized_scope_type = _normalize_upload_scope_type(scope_type)
        effective_scope_id = _resolve_scope_id(
            normalized_scope_type, scope_id, project_name
        )
        effective_scope_id = _validate_storage_segment(effective_scope_id, "scope_id")
        normalized_document_type = _normalize_document_type(document_type)
        normalized_project_type = normalize_project_type(project_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if normalized_scope_type == "project":
        project_info = upsert_project(
            effective_scope_id, project_type=normalized_project_type
        )
        effective_project_name = project_info["project_name"]
        effective_project_type = project_info["project_type"]
        project_path = os.path.join(BASE_DIR, "projects", effective_scope_id, "files")
        text_path = os.path.join(BASE_DIR, "projects", effective_scope_id, "text")
    else:
        effective_project_name = f"{normalized_scope_type}:{effective_scope_id}"
        effective_project_type = normalized_project_type or "geplant"
        scope_base_path = os.path.join(
            BASE_DIR, "scopes", normalized_scope_type, effective_scope_id
        )
        project_path = os.path.join(scope_base_path, "files")
        text_path = os.path.join(scope_base_path, "text")

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(text_path, exist_ok=True)

    extracted_texts = []
    metadatas = []
    uploaded_file_records = []

    for file in files:
        file_path = os.path.join(project_path, file.filename)
        with open(file_path, "wb") as saved_file:
            saved_file.write(await file.read())

        try:
            text = extract_text_from_file(file_path)
        except Exception as exc:
            try:
                add_document_record(
                    project_name=effective_project_name,
                    source_filename=file.filename,
                    stored_file_path=file_path,
                    stored_text_path="",
                    file_size_bytes=os.path.getsize(file_path)
                    if os.path.exists(file_path)
                    else None,
                    chunks_indexed=0,
                    extraction_status="error",
                    error_message=str(exc),
                    project_type=effective_project_type,
                    scope_type=normalized_scope_type,
                    scope_id=effective_scope_id,
                    document_type=normalized_document_type,
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=422,
                detail=f"Failed to process '{file.filename}': {exc}",
            )

        if not text or not text.strip():
            try:
                add_document_record(
                    project_name=effective_project_name,
                    source_filename=file.filename,
                    stored_file_path=file_path,
                    stored_text_path="",
                    file_size_bytes=os.path.getsize(file_path)
                    if os.path.exists(file_path)
                    else None,
                    chunks_indexed=0,
                    extraction_status="error",
                    error_message="Extracted text is empty.",
                    project_type=effective_project_type,
                    scope_type=normalized_scope_type,
                    scope_id=effective_scope_id,
                    document_type=normalized_document_type,
                )
            except Exception:
                pass
            raise HTTPException(
                status_code=422,
                detail=f"Failed to process '{file.filename}': extracted text is empty.",
            )

        extracted_texts.append(text)
        metadatas.append(
            {
                "source": file.filename,
                "project_name": effective_project_name,
                "project_type": effective_project_type,
                "scope_type": normalized_scope_type,
                "scope_id": effective_scope_id,
                "document_type": normalized_document_type,
            }
        )

        text_file_path = os.path.join(text_path, f"{file.filename}.txt")
        with open(text_file_path, "w", encoding="utf-8") as text_file:
            text_file.write(text)

        uploaded_file_records.append(
            {
                "source_filename": file.filename,
                "stored_file_path": file_path,
                "stored_text_path": text_file_path,
                "file_size_bytes": os.path.getsize(file_path)
                if os.path.exists(file_path)
                else None,
            }
        )

    documents = split_text(extracted_texts, metadatas=metadatas)
    add_documents_to_scope(
        scope_type=normalized_scope_type,
        scope_id=effective_scope_id,
        documents=documents,
        project_name=effective_project_name,
        project_type=effective_project_type,
        document_type=normalized_document_type,
    )

    graph_status = "not_indexed"
    graph_error_message = None
    graph_last_indexed_at = None
    try:
        graph_result = ingest_upload_to_graph(
            project_name=effective_project_name,
            project_type=effective_project_type,
            scope_type=normalized_scope_type,
            scope_id=effective_scope_id,
            document_type=normalized_document_type,
            uploaded_file_records=uploaded_file_records,
            documents=documents,
        )
        graph_status = str(graph_result.get("status", "not_indexed"))
        if graph_status == "indexed":
            graph_last_indexed_at = datetime.now(timezone.utc).replace(microsecond=0)
    except Exception as exc:
        graph_status = "error"
        graph_error_message = str(exc)

    chunks_per_source: dict[str, int] = {}
    for doc in documents:
        source = (doc.metadata or {}).get("source")
        if source:
            chunks_per_source[source] = chunks_per_source.get(source, 0) + 1

    for record in uploaded_file_records:
        try:
            add_document_record(
                project_name=effective_project_name,
                source_filename=record["source_filename"],
                stored_file_path=record["stored_file_path"],
                stored_text_path=record["stored_text_path"],
                file_size_bytes=record["file_size_bytes"],
                chunks_indexed=chunks_per_source.get(record["source_filename"], 0),
                extraction_status="indexed",
                error_message=None,
                graph_status=graph_status,
                graph_last_indexed_at=graph_last_indexed_at,
                graph_error_message=graph_error_message,
                project_type=effective_project_type,
                scope_type=normalized_scope_type,
                scope_id=effective_scope_id,
                document_type=normalized_document_type,
            )
        except Exception:
            # Upload flow should continue even if metadata DB is temporarily unavailable.
            pass

    return {
        "message": "Files uploaded, processed and indexed successfully",
        "project_name": effective_project_name,
        "project_type": effective_project_type,
        "scope_type": normalized_scope_type,
        "scope_id": effective_scope_id,
        "document_type": normalized_document_type,
        "chunks_created": len(documents),
    }


class ChatRequest(BaseModel):
    query: str
    scope: str = Field(default="project")
    project_name: str | None = None
    top_k: int = Field(default=4, ge=1, le=10)
    scope_type_filter: str | None = None
    scope_id_filter: str | None = None
    document_type_filter: str | None = None


@app.post("/chat")
async def chat(request: ChatRequest):
    metadata_filters = {
        "scope_type": request.scope_type_filter,
        "scope_id": request.scope_id_filter,
        "document_type": request.document_type_filter,
    }

    try:
        scope_context = resolve_chat_scope(
            scope=request.scope,
            project_name=request.project_name,
            query=request.query,
            top_k=request.top_k,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    graph_result = get_graph_context_for_chat(
        query=request.query,
        scope=scope_context["scope"],
        project_name=request.project_name,
    )

    if scope_context["mode"] == "vectorstore":
        result = generate_answer(
            vectorstore=scope_context["vectorstore"],
            query=request.query,
            top_k=request.top_k,
            metadata_filters=metadata_filters,
            graph_context=graph_result["graph_context"],
            graph_facts=graph_result["graph_facts"],
        )
    else:
        filtered_docs = apply_metadata_filters(
            scope_context["retrieved_documents"],
            metadata_filters=metadata_filters,
        )
        result = generate_answer_from_documents(
            query=request.query,
            retrieved_documents=filtered_docs[: request.top_k],
            graph_context=graph_result["graph_context"],
            graph_facts=graph_result["graph_facts"],
        )

    result["scope"] = scope_context["scope"]
    result["effective_scope"] = scope_context["effective_scope"]
    result["filters_applied"] = {
        key: value
        for key, value in metadata_filters.items()
        if value is not None and str(value).strip()
    }
    return result


@app.get("/projects")
async def get_projects():
    projects = list_projects()
    return {"projects": projects, "count": len(projects)}


@app.get("/system/knowledge-status")
async def get_system_knowledge_status():
    return get_knowledge_status()


@app.get("/projects/list")
async def get_projects_list():
    return await get_projects()


@app.get("/projects/info")
async def get_projects_info(project_name: str):
    return await get_project_info(project_name)


@app.get("/projects/{project_name}")
async def get_project_info(project_name: str):
    if not project_name or not project_name.strip():
        raise HTTPException(status_code=422, detail="Project name is required.")

    project = get_project(project_name)
    if project is None:
        raise HTTPException(
            status_code=404, detail=f"Project '{project_name}' not found."
        )

    return project
