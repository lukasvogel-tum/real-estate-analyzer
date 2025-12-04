from fastapi import FastAPI, File, UploadFile, Form
from pydantic import BaseModel
import os
from utils.extract_text import extract_text_from_file


class ProjectCreateRequest(BaseModel):
    project_id: str

class ProjectUploadRequest(BaseModel):
    project_id: str


# FastAPI-App starten
app = FastAPI()

# --- Datamodell für Chat-Anfragen ---
class ChatRequest(BaseModel):
    message: str          # die Nachricht vom Benutzer
    project_id: str | None = None  # später für "pro Immobilie"

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

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload")
async def upload_file(
    project_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Speichert eine Datei in einem bestimmten Projekt und extrahiert den Text.
    """

    # Projektpfade
    project_path = os.path.join("projects", project_id)
    files_path = os.path.join(project_path, "files")
    text_path = os.path.join(project_path, "text")

    # Prüfen, ob Projekt existiert
    if not os.path.exists(project_path):
        return {"error": f"Projekt '{project_id}' existiert nicht. Bitte zuerst /create_project verwenden."}

    # Datei speichern
    file_path = os.path.join(files_path, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Text extrahieren
    extracted_text = extract_text_from_file(file_path)

    # Textspeicherung
    text_file_path = os.path.join(text_path, f"{file.filename}.txt")
    with open(text_file_path, "w", encoding="utf-8") as t:
        t.write(extracted_text)

    return {
        "message": f"Datei '{file.filename}' wurde erfolgreich im Projekt '{project_id}' gespeichert.",
        "saved_file": file_path,
        "saved_text": text_file_path,
        "text_preview": extracted_text[:500]
    }


