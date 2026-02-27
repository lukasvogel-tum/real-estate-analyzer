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
- Projektbezogener Chat mit nachvollziehbarer Antwort:
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
- RAG: LangChain (LCEL)
- Vector DB: LanceDB (lokal persistent)
- Embeddings: OpenAI (`OPENAI_API_KEY` via Windows ENV)
- Chunking: RecursiveCharacterTextSplitter
- Testing/Clients: Postman
- Spaeter:
  - Frontend: Vercel Deployment
  - CI/CD: GitLab

---

## 2) Ist-Stand (Heute)

Stand: 2026-02-25

### 2.1 Implementierte Kernfunktionen

#### Upload-Pipeline (`POST /upload`)
- Nimmt `files[]` + `project_name` (FormData)
- Optional: `project_type` (`bestand` | `potenziell`)
- Speichert Dateien unter `backend/projects/<project>/files/`
- Extrahiert Text:
  - PDF via `PyPDFLoader`
  - Sonst Plain-Text Read
- Speichert Text-Backup unter `backend/projects/<project>/text/`
- Chunkt mit `RecursiveCharacterTextSplitter`:
  - `chunk_size=1000`
  - `chunk_overlap=100`
- Indexiert Chunks in LanceDB pro Projekt-Tabelle
- Schreibt/Aktualisiert Projekt-Metadaten in `backend/projects/_registry.json`
- Chunk-Metadaten aktuell:
  - `source` (Dateiname)

#### Chat-RAG (`POST /chat`)
- Request:
  - `project_name` (string)
  - `query` (string)
  - `top_k` (optional, default `4`, valid `1..10`)
- Verhalten:
  - Laedt projektbezogenen VectorStore
  - Bei unbekanntem Projekt: HTTP `404`
  - Retrieval mit `top_k` (bevorzugt mit Relevance Scores, sonst Fallback ohne Score)
  - Antwortgenerierung via LCEL + `gpt-4o-mini`
- Response:
  - `answer`
  - `sources` (dedupliziert, stabile Reihenfolge)
  - `evidence[]` mit:
    - `source`
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
  - `GET /projects/{project_name}` fuer Projekt-Detailinfos
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
  - Laden/Hinzufuegen von Dokumenten
  - Persistenter DB-Pfad ist explizit auf `backend/lancedb` verankert (kein CWD-Zufall)
  - Schema-Konflikt-Fallback (Drop + Rebuild)
- `backend/services/rag.py`
  - Retrieval + LCEL-Chain
  - Evidence- und Source-Aufbereitung
- `backend/services/project_registry.py`
  - Registry-Datei lesen/schreiben
  - Projekt-Typ validieren
  - Projekte discovern/listen/detaillieren
  - Projektstatistiken aggregieren
- `backend/utils/extract_file.py`
  - Dateiextraktion (PDF + Plain Text)
- `backend/utils/text_splitter.py`
  - Text zu `Document`-Chunks
- `backend/utils/embeddings.py`
  - OpenAI Embeddings Initialisierung

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

#### `POST /chat`
- Input: JSON
```json
{
  "project_name": "TestProject",
  "query": "Welche Risiken und Chancen hat das Objekt?",
  "top_k": 4
}
```
- Erfolgsantwort:
```json
{
  "answer": "...",
  "sources": ["file1.pdf", "file2.pdf"],
  "evidence": [
    {
      "source": "file1.pdf",
      "excerpt": "...",
      "chunk_id": null,
      "score": 0.87
    }
  ]
}
```
- Fehler:
  - `404` bei unbekanntem Projekt/fehlender Tabelle
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

### 2.4 MVP-Readiness (kurz)
Bereits vorhanden:
- Projektbezogener Upload + persistente Vektorindexierung
- Projektbezogener Chat mit nachvollziehbarer Evidenz

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

