import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from services.metadata_db import add_document_record, init_metadata_db
from services.project_registry import (
    get_project,
    list_projects,
    normalize_project_type,
    upsert_project,
)
from services.rag import generate_answer, generate_answer_from_documents
from services.scope_retriever import resolve_chat_scope
from services.vectorstore import add_documents_to_project
from utils.extract_file import extract_text_from_file
from utils.text_splitter import split_text

load_dotenv()

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


@app.on_event("startup")
def startup_event() -> None:
    init_metadata_db()


@app.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    project_name: str = Form(...),
    project_type: str | None = Form(default=None),
):
    if not project_name:
        raise HTTPException(status_code=422, detail="Project name is required.")

    if not files or len(files) == 0:
        raise HTTPException(status_code=422, detail="No files provided.")

    try:
        normalized_project_type = normalize_project_type(project_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    project_info = upsert_project(project_name, project_type=normalized_project_type)
    effective_project_type = project_info["project_type"]

    project_path = os.path.join(BASE_DIR, "projects", project_name, "files")
    text_path = os.path.join(BASE_DIR, "projects", project_name, "text")

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
        except ValueError as exc:
            try:
                add_document_record(
                    project_name=project_name,
                    source_filename=file.filename,
                    stored_file_path=file_path,
                    stored_text_path="",
                    file_size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else None,
                    chunks_indexed=0,
                    extraction_status="error",
                    error_message=str(exc),
                    project_type=effective_project_type,
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
                    project_name=project_name,
                    source_filename=file.filename,
                    stored_file_path=file_path,
                    stored_text_path="",
                    file_size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else None,
                    chunks_indexed=0,
                    extraction_status="error",
                    error_message="Extracted text is empty.",
                    project_type=effective_project_type,
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
                "project_name": project_name,
                "project_type": effective_project_type,
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
                "file_size_bytes": os.path.getsize(file_path) if os.path.exists(file_path) else None,
            }
        )

    documents = split_text(extracted_texts, metadatas=metadatas)
    add_documents_to_project(
        project_name=project_name,
        documents=documents,
        project_type=effective_project_type,
    )

    chunks_per_source: dict[str, int] = {}
    for doc in documents:
        source = (doc.metadata or {}).get("source")
        if source:
            chunks_per_source[source] = chunks_per_source.get(source, 0) + 1

    for record in uploaded_file_records:
        try:
            add_document_record(
                project_name=project_name,
                source_filename=record["source_filename"],
                stored_file_path=record["stored_file_path"],
                stored_text_path=record["stored_text_path"],
                file_size_bytes=record["file_size_bytes"],
                chunks_indexed=chunks_per_source.get(record["source_filename"], 0),
                extraction_status="indexed",
                error_message=None,
                project_type=effective_project_type,
            )
        except Exception:
            # Upload flow should continue even if metadata DB is temporarily unavailable.
            pass

    return {
        "message": "Files uploaded, processed and indexed successfully",
        "project_name": project_name,
        "project_type": effective_project_type,
        "chunks_created": len(documents),
    }


class ChatRequest(BaseModel):
    query: str
    scope: str = Field(default="project")
    project_name: str | None = None
    top_k: int = Field(default=4, ge=1, le=10)


@app.post("/chat")
async def chat(request: ChatRequest):
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

    if scope_context["mode"] == "vectorstore":
        result = generate_answer(
            vectorstore=scope_context["vectorstore"],
            query=request.query,
            top_k=request.top_k,
        )
    else:
        result = generate_answer_from_documents(
            query=request.query,
            retrieved_documents=scope_context["retrieved_documents"],
        )

    result["scope"] = scope_context["scope"]
    result["effective_scope"] = scope_context["effective_scope"]
    return result


@app.get("/projects")
async def get_projects():
    projects = list_projects()
    return {"projects": projects, "count": len(projects)}


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
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")

    return project
