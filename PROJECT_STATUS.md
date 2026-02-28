# Real Estate Analyzer - Produkt- und Projektstatus

## Zweck dieses Dokuments
Dieses Dokument ist die zentrale, laufend gepflegte Referenz fuer:
1. Zielbild (Vision, Funktionen, Architektur, Tech Stack)
2. Aktueller Stand (implementierte Funktionen, APIs, Module, bekannte Luecken)

Pflege-Regel:
- Bei jeder funktionalen oder architektonischen Aenderung dieses Dokument im gleichen Schritt aktualisieren.
- Ziel: jederzeit schneller Ueberblick fuer "vibe coding" mit Kontrolle.

---

## 1) Zielbild (Soll-Zustand)

### 1.1 Produktvision
Ein professioneller Family-Office-Real-Estate Assistant mit:
- Projektkategorien:
  - Bestand
  - Potenzielle Objekte
- Projekt-spezifischem Chat:
  - Jeder Chat nutzt nur den RAG-Kontext des ausgewaehlten Projekts.
- Spaetere Erweiterungen:
  - Cloud-Storage Integrationen (Google Drive, OneDrive, Dropbox)
  - Externe Datenquellen (z. B. Bevoelkerungswachstum, Standortmetriken)
  - Graphdatenbank fuer Wissens- und Beziehungsmodell
  - Asset-Uebersicht und steuerliche Perspektive
  - Evaluation Agent fuer strukturierte Objektbewertung

### 1.2 Ziel-Funktionsumfang
Phase 1 (MVP-RAG, jetzt relevant):
- Dokumente hochladen, extrahieren, chunken, indexieren (projektbezogen)
- Scope-basierter Chat mit nachvollziehbarer Antwort:
  - `scope`: `project` | `realestate_global` | `global` (MVP: `global` nutzt Immobilien-Index)
  - `answer`
  - `sources` (dedupliziert)
  - `evidence` (Auszuege aus echten Retrieval-Treffern)

Phase 2 (naechster Ausbau):
- Projekt-Registry:
  - `project_type` (`bestand` | `potenziell`)
  - Endpoints fuer Liste und Projekt-Infos
  - Persistente Projekt-Metadaten (JSON-Registry)

Phase 3 (Agent-Layer):
- Evaluation Agent:
  - Bewertung von Lage, Zustand, Risiken, Kennzahlen
  - Offene Fragen und Due-Diligence-Checklisten

### 1.3 Ziel-Architektur
- `main.py`: nur API-Routen + Orchestrierung
- `services/`: Business-Logik (RAG, VectorStore, spaeter Agenten)
- `utils/`: technische Utilities (Extraction, Splitting, Embeddings)
- Datenhaltung:
  - `backend/projects/<project>/files` fuer Originaldateien
  - `backend/projects/<project>/text` fuer Text-Backups
  - `backend/lancedb/` fuer persistente Vektordaten

### 1.4 Ziel-Tech-Stack
- Backend: Python + FastAPI
- Frontend: Next.js (App Router) + TypeScript
- RAG: LangChain (LCEL)
- Metadata DB: SQLAlchemy (Postgres-ready, lokaler SQLite-Fallback fuer MVP)
- Vector DB: LanceDB (lokal persistent)
- Embeddings: OpenAI (`OPENAI_API_KEY` via Windows ENV)
- Chunking: RecursiveCharacterTextSplitter
- Testing/Clients: Postman
- Deployment (langfristig):
  - Docker Compose als moegliche Deployment-Option fuer kontrollierte Umgebungen
- Spaeter:
  - Frontend: Vercel Deployment
  - CI/CD: GitLab

---

## 2) Ist-Stand (Heute)

Stand: 2026-02-28

### 2.1 Implementierte Kernfunktionen

#### Upload-Pipeline (`POST /upload`)
- Nimmt `files[]` + `project_name` (FormData)
- Optional: `project_type` (`bestand` | `potenziell`)
- Speichert Dateien unter `backend/projects/<project>/files/`
- Extrahiert Text:
  - PDF via `PyPDFLoader`
  - DOCX via `python-docx`
  - XLSX via `openpyxl`
  - PPTX via `python-pptx`
  - TXT/MD via Plain-Text Read
  - CSV via `csv` parser
- Speichert Text-Backup unter `backend/projects/<project>/text/`
- Chunkt mit `RecursiveCharacterTextSplitter`:
  - `chunk_size=1000`
  - `chunk_overlap=100`
- Indexiert Chunks in LanceDB pro Projekt-Tabelle
- Spiegelt Chunks zusaetzlich in shared Tabelle `realestate_global` (Option B)
- Schreibt/Aktualisiert Projekt-Metadaten in `backend/projects/_registry.json`
- Schreibt Upload- und Dateimetadaten in SQL Metadata DB (`projects`, `documents`)
- Chunk-Metadaten aktuell:
  - `source` (Dateiname)
  - `project_name`
  - `project_type`

#### Chat-RAG (`POST /chat`)
- Request:
  - `query` (string)
  - `scope` (`project` | `realestate_global` | `global`, default `project`)
  - `project_name` (string, Pflicht wenn `scope=project`)
  - `top_k` (optional, default `4`, valid `1..10`)
- Verhalten:
  - Scope `project`: nutzt projektspezifischen VectorStore
  - Scope `realestate_global`: nutzt shared Tabelle `realestate_global`
  - Scope `global`: nutzt fuer MVP denselben shared Immobilien-Index
  - Fallback: falls shared Tabelle noch nicht vorhanden ist, Fanout-Retrieval ueber alle Projekt-Tabellen
  - Bei unbekanntem Projekt oder fehlenden Daten: HTTP `404`
  - Retrieval mit `top_k` (bevorzugt mit Relevance Scores, sonst Fallback ohne Score)
  - Antwortgenerierung via LCEL + `gpt-4o-mini`
- Response:
  - `answer`
  - `scope`
  - `effective_scope`
  - `sources` (dedupliziert, stabile Reihenfolge)
  - `evidence[]` mit:
    - `source`
    - `file_name`
    - `project_name`
    - `project_type`
    - `excerpt` (max 400 Zeichen)
    - `chunk_id` (falls in Metadaten vorhanden, sonst `null`)
    - `score` (falls verfuegbar, sonst `null`)

#### Projekt-Registry
- Metadaten-Store:
  - Datei `backend/projects/_registry.json`
  - Felder: `project_name`, `project_type`, `created_at`, `updated_at`
- Auto-Discovery:
  - Bestehende Projekte aus `backend/projects/` Ordnern
  - Bestehende LanceDB-Tabellen
- Endpoints:
  - `GET /projects` fuer Projektliste inkl. Basisstatistiken
  - `GET /projects/list` als Alias (Postman-kompatibel)
  - `GET /projects/{project_name}` fuer Projekt-Detailinfos
  - `GET /projects/info?project_name=...` als Alias (Postman-kompatibel)
- Projekt-Statistiken im Response:
  - `files_count`
  - `text_backups_count`
  - `table_name`
  - `has_vector_index`
  - `chunks_indexed`

### 2.2 Aktuelle Modulstruktur
- `backend/main.py`
  - API-Endpunkte (`/upload`, `/chat`)
  - Request-Validierung und Orchestrierung
- `backend/services/vectorstore.py`
  - Projekt-Tabellen in LanceDB
  - Shared Immobilien-Index `realestate_global`
  - Laden/Hinzufuegen von Dokumenten
  - Persistenter DB-Pfad ist explizit auf `backend/lancedb` verankert (kein CWD-Zufall)
  - Schema-Konflikt-Fallback (Drop + Rebuild)
- `backend/services/rag.py`
  - Retrieval + LCEL-Chain (VectorStore oder vorab aggregierte Treffer)
  - Evidence- und Source-Aufbereitung
- `backend/services/scope_retriever.py`
  - Scope-Normalisierung und Scope-Routing fuer Chat
  - Fallback-Retrieval ueber mehrere Projekt-Tabellen
- `backend/services/project_registry.py`
  - Registry-Datei lesen/schreiben
  - Projekt-Typ validieren
  - Projekte discovern/listen/detaillieren
  - Projektstatistiken aggregieren
- `backend/services/metadata_db.py`
  - SQLAlchemy Engine + Schema fuer `projects` und `documents`
  - Postgres-kompatibel via `DATABASE_URL` (MVP default: lokale SQLite DB)
  - Upload-Metadaten und Projekt-Metadaten persistieren
- `backend/utils/extract_file.py`
  - Dateiextraktion (PDF, DOCX, XLSX, PPTX, TXT, MD, CSV)
- `backend/utils/text_splitter.py`
  - Text zu `Document`-Chunks
- `backend/utils/embeddings.py`
  - OpenAI Embeddings Initialisierung
- `frontend/app/*`
  - UI-Routing fuer Projects, Project Detail und Workspace
- `frontend/components/UploadForm.tsx`
  - Upload-Flow fuer projektbezogenes Indexing
- `frontend/components/ScopeChatPanel.tsx`
  - Scope-Chat UI fuer `project`, `realestate_global`, `global`
- `frontend/lib/api.ts`
  - API-Client fuer FastAPI-Endpoints

### 2.3 Aktuelle API-Contracts

#### `POST /upload`
- Input: FormData
  - `project_name`: string
  - `project_type`: optional, `bestand` | `potenziell`
  - `files`: 1..n Dateien
- Erfolgsantwort:
  - `message`
  - `project_name`
  - `project_type`
  - `chunks_created`
- Fehler:
  - `422` bei unsupported Dateityp
  - `422` bei leerer/fehlgeschlagener Extraktion

#### `POST /chat`
- Input: JSON
```json
{
  "scope": "project",
  "project_name": "TestProject",
  "query": "Welche Risiken und Chancen hat das Objekt?",
  "top_k": 4
}
```
- Erfolgsantwort:
```json
{
  "answer": "...",
  "scope": "project",
  "effective_scope": "project",
  "sources": ["TestProject/file1.pdf", "TestProject/file2.pdf"],
  "evidence": [
    {
      "source": "TestProject/file1.pdf",
      "file_name": "file1.pdf",
      "project_name": "TestProject",
      "project_type": "potenziell",
      "excerpt": "...",
      "chunk_id": null,
      "score": 0.87
    }
  ]
}
```
- Fehler:
  - `404` bei unbekanntem Projekt/fehlender Tabelle
  - `404` bei leerem shared Scope ohne Indexdaten
  - `422` bei ungueltigen Inputs (z. B. `top_k` ausserhalb `1..10`)

#### `GET /projects`
- Erfolgsantwort:
```json
{
  "projects": [
    {
      "project_name": "TestProject",
      "project_type": "potenziell",
      "created_at": "2026-02-25T14:00:00+00:00",
      "updated_at": "2026-02-25T14:10:00+00:00",
      "files_count": 3,
      "text_backups_count": 3,
      "table_name": "testproject",
      "has_vector_index": true,
      "chunks_indexed": 120
    }
  ],
  "count": 1
}
```

#### `GET /projects/{project_name}`
- Erfolgsantwort:
  - Ein einzelnes Projektobjekt (gleiches Schema wie in `GET /projects`)
- Fehler:
  - `404` wenn Projekt nicht gefunden
  - `422` bei leerem Projektnamen

#### `GET /projects/list`
- Alias auf `GET /projects` (gleiches Response-Schema)

#### `GET /projects/info`
- Query-Param:
  - `project_name` (string, Pflicht)
- Alias auf `GET /projects/{project_name}` (gleiches Response-Schema)

### 2.4 MVP-Readiness (kurz)
Bereits vorhanden:
- Projektbezogener Upload + persistente Vektorindexierung
- Projektbezogener Chat mit nachvollziehbarer Evidenz
- Frontend-MVP fuer Upload, Projektliste, Projekt-Chat und Workspace-Scopes
- Metadata-DB-Layer fuer Projekte und Upload-Dokumente (SQLAlchemy)

Noch offen fuer robustes MVP im Einsatz:
- Einheitliche Error-Struktur auf allen Endpunkten
- Minimales Logging/Observability
- Optional: echte `chunk_id`-Vergabe beim Chunking

---

## 3) Arbeitsregeln fuer schnelle, kontrollierte Weiterentwicklung
- Kleine, pruefbare Aenderungsschritte
- `main.py` schlank halten (keine Business-Logik)
- Keine grossen Refactors ohne explizites OK
- Nach jeder Aenderung: kurze Testanleitung (Uvicorn + Postman)
- Dieses Dokument bei jeder relevanten Aenderung aktualisieren

---

## 4) Verbindliche Leitlinie fuer die Zusammenarbeit
- Ziel ist ein `industry standard`, `state of the art` Projekt, das gleichzeitig fuer dich nachvollziehbar und lernbar bleibt.
- Jede relevante Aenderung wird mit kurzem `Warum` dokumentiert (Trade-off, Alternative, Entscheidung).
- Bevorzugt werden klare, wartbare Loesungen statt unnoetig komplexer "cleverer" Implementierungen.
- Architektur- und API-Entscheidungen werden konsistent gehalten und bei Aenderungen in diesem Dokument aktualisiert.
- Wenn eine Best-Practice-Loesung unnoetig kompliziert waere, wird eine pragmatische Zwischenstufe gewaehlt und als naechster Schritt markiert.
- Branch-First ist Standard: Entwicklung in `feat/*`, `fix/*`, `chore/*`, Merge nach `main` ueber PR.
- Direkte Commits auf `main` nur in klar begruendeten Ausnahmefaellen (z. B. akuter Hotfix).

