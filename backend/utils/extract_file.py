import os
import docx
import PyPDF2

def extract_text_from_file(file_path: str) -> str:
    """
    Extrahiert Text aus PDF, DOCX und TXT Dateien.
    """
    ext = os.path.splitext(file_path)[1].lower()

    # ---- TXT ----
    if ext == ".txt":
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    # ---- DOCX ----
    if ext == ".docx":
        doc = docx.Document(file_path)
        return "\n".join([p.text for p in doc.paragraphs])

    # ---- PDF ----
    if ext == ".pdf":
        text = ""
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text

    # ---- Unbekannt ----
    return "Dieser Dateityp wird noch nicht unterstützt."
