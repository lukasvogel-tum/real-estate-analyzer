from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
import os
import chromadb
from utils.extract_file import extract_text_from_file
from utils.embeddings import embed_text
from utils.text_splitter import split_into_chunks


# ---- Chroma-Client ----
chroma_client = chromadb.Client()
collection = chroma_client.get_or_create_collection("documents")


class ProjectCreateRequest(BaseModel):
    project_id: str


# FastAPI-App starten
app = FastAPI()


# --- Datamodell für Chat-Anfragen ---
class ChatRequest(BaseModel):
    message: str          # die Nachricht vom Benutzer
    project_id: str | None = None  # später für "pro Immobilie"


class SearchRequest(BaseModel):
    query: str
    project_id: str
    top_k: int = 3


# --- Routen ---
@app.post("/create_project")
def create_project(req: ProjectCreateRequest):

    project_path = os.path.join("projects", req.project_id)
    files_path = os.path.join(project_path, "files")
    text_path = os.path.join(project_path, "text")

    # Ordnerstruktur anlegen
    os.makedirs(files_path, exist_ok=True)
    os.makedirs(text_path, exist_ok=True)

    return {
        "message": f"Projekt '{req.project_id}' wurde erstellt.",
        "folders": [files_path, text_path]
    }


@app.get("/")
def read_root():
    return {"message": "Backend läuft!"}


@app.post("/chat")
def chat(req: ChatRequest):
    """
    Simulierter Chat-Endpunkt.
    Später kommt hier OpenAI, RAG usw. rein.
    """
    if req.project_id:
        return {"answer": f"Du fragst zum Projekt '{req.project_id}': {req.message}"}
    else:
        return {"answer": f"Du fragst allgemein: {req.message}"}
    
@app.post("/search")
def search(req: SearchRequest):
    """
    Sucht in den gespeicherten Dokumenten eines Projekts
    nach ähnlichen Stellen zur Query.
    """

    # 1) Query in Embedding umwandeln
    query_embedding = embed_text(req.query)
    
    # 2) Chroma abfragen – nur in diesem Projekt
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=req.top_k,
        where={"project_id": req.project_id}
    )

    # 3) Chroma-Ergebnis etwas hübscher machen
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    dists = results.get("distances", [[]])[0] if "distances" in results else [None] * len(docs)

    hits = []
    for doc, meta, dist in zip(docs, metas, dists):
        hits.append({
            "text": doc,
            "filename": meta.get("filename") if meta else None,
            "project_id": meta.get("project_id") if meta else None,
            "distance": float(dist) if dist is not None else None
        })

    return {
        "query": req.query,
        "project_id": req.project_id,
        "results": hits
    }


@app.post("/upload")
async def upload_file(
    project_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Speichert eine Datei im Projekt, extrahiert Text,
    erzeugt ein Embedding und speichert alles in Chroma.
    """

    # Projektpfade
    project_path = os.path.join("projects", project_id)
    files_path = os.path.join(project_path, "files")
    text_path = os.path.join(project_path, "text")

    # Prüfen, ob Projekt existiert
    if not os.path.exists(project_path):
        return {
            "error": (
                f"Projekt '{project_id}' existiert nicht. "
                f"Bitte zuerst /create_project verwenden."
            )
        }

    # Datei speichern
    file_path = os.path.join(files_path, file.filename)
    os.makedirs(files_path, exist_ok=True)
    os.makedirs(text_path, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(await file.read())

   # Text extrahieren
    extracted_text = extract_text_from_file(file_path)

    # --- Text in Chunks zerlegen ---
    chunks = split_into_chunks(extracted_text, chunk_size=500, overlap=100)

    # Für jeden Chunk Embedding erzeugen und speichern
    for i, chunk in enumerate(chunks):
        embedding = embed_text(chunk)

        collection.add(
            documents=[chunk],
            embeddings=[embedding],
            ids=[f"{project_id}_{file.filename}_chunk{i}"],
            metadatas=[{
                "project_id": project_id,
                "filename": file.filename,
                "chunk_index": i
            }]
    )


    # Textspeicherung
    text_file_path = os.path.join(text_path, f"{file.filename}.txt")
    with open(text_file_path, "w", encoding="utf-8") as t:
        t.write(extracted_text)

    return {
        "message": (
            f"Datei '{file.filename}' wurde erfolgreich "
            f"im Projekt '{project_id}' gespeichert."
        ),
        "saved_file": file_path,
        "saved_text": text_file_path,
        "text_preview": extracted_text[:500],
        "embedding_size": len(embedding)
    }
