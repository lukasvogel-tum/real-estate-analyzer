import os
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Services
from services.vectorstore import add_documents_to_project, get_vectorstore
from services.rag import generate_answer
from services.project_registry import (
    get_project,
    list_projects,
    normalize_project_type,
    upsert_project,
)

# Utils
from utils.text_splitter import split_text
from utils.extract_file import extract_text_from_file

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


@app.post("/upload")
async def upload_files(
    files: list[UploadFile] = File(...),
    project_name: str = Form(...),
    project_type: str | None = Form(default=None),
):
    if not project_name:
        raise HTTPException(status_code=422, detail="Project name is required.")

    try:
        normalized_project_type = normalize_project_type(project_type)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    project_path = os.path.join(BASE_DIR, "projects", project_name, "files")
    text_path = os.path.join(BASE_DIR, "projects", project_name, "text")

    os.makedirs(project_path, exist_ok=True)
    os.makedirs(text_path, exist_ok=True)

    if not files or len(files) == 0:
        raise HTTPException(status_code=422, detail="No files provided.")

    extracted_texts = []
    metadatas = []

    for file in files:
        # 1. Datei speichern
        file_path = os.path.join(project_path, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        # 2. Text extrahieren
        text = extract_text_from_file(file_path)
        extracted_texts.append(text)
        metadatas.append({"source": file.filename})
        
        # (Optional) Text-Backup speichern
        text_file_path = os.path.join(text_path, f"{file.filename}.txt")
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(text)

    # 3. Text in Chunks splitten
    documents = split_text(extracted_texts, metadatas=metadatas)

    # 4. Embeddings erzeugen und in LanceDB speichern
    add_documents_to_project(project_name, documents)
    project_info = upsert_project(project_name, project_type=normalized_project_type)

    return {
        "message": "Files uploaded, processed and indexed successfully", 
        "project_name": project_name,
        "project_type": project_info["project_type"],
        "chunks_created": len(documents)
    }


class ChatRequest(BaseModel):
    project_name: str
    query: str
    top_k: int = Field(default=4, ge=1, le=10)

@app.post("/chat")
async def chat_with_project(request: ChatRequest):
    if not request.project_name:
        raise HTTPException(status_code=422, detail="Project name is required.")

    # 1. VectorStore laden (ohne Files neu zu lesen)
    vectorstore = get_vectorstore(request.project_name)
    
    if not vectorstore:
        raise HTTPException(
            status_code=404,
            detail=f"Project '{request.project_name}' not found or has no indexed documents.",
        )

    # 2. Antwort generieren
    result = generate_answer(vectorstore, request.query, top_k=request.top_k)
    
    return result


@app.get("/projects")
async def get_projects():
    projects = list_projects()
    return {"projects": projects, "count": len(projects)}


@app.get("/projects/{project_name}")
async def get_project_info(project_name: str):
    if not project_name or not project_name.strip():
        raise HTTPException(status_code=422, detail="Project name is required.")

    project = get_project(project_name)
    if project is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_name}' not found.")

    return project
