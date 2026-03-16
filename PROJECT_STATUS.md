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
  - Geplante Objekte
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
  - `scope`: `project` | `realestate_global` | `global` (`global` nutzt `global_brain`)
  - `answer`
  - `sources` (dedupliziert)
  - `evidence` (Auszuege aus echten Retrieval-Treffern)

Phase 2 (naechster Ausbau):
- Projekt-Registry:
  - `project_type` (`bestand` | `geplant`)
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
- Frontend: Next.js (App Router) + TypeScript + TailwindCSS + shadcn/ui (Radix)
- RAG: LangChain (LCEL)
- Metadata DB: SQLAlchemy (Postgres-ready, lokaler SQLite-Fallback fuer MVP)
- Vector DB: LanceDB (lokal persistent)
- Graph DB: Neo4j (Foundation fuer Entitaeten- und Beziehungswissen)
- Embeddings: OpenAI (`OPENAI_API_KEY` via Windows ENV)
- Chunking: RecursiveCharacterTextSplitter
- Testing/Clients: Postman
- Deployment (langfristig):
  - Docker Compose als moegliche Deployment-Option fuer kontrollierte Umgebungen
  - Lokale Neo4j-Entwicklung via `docker-compose.yml`
- Spaeter:
  - Frontend: Vercel Deployment
  - CI/CD: GitLab

---

## 2) Ist-Stand (Heute)

Stand: 2026-03-03

### 2.1 Implementierte Kernfunktionen

#### Frontend App Shell + Design System (Next.js)
- UI auf konsistenten SaaS-Style umgestellt:
  - App Shell mit Sidebar + Topbar + zentralem Content-Bereich
  - Einheitliche Tokens fuer Farben, Radius, Shadows und Typografie
  - TailwindCSS als Styling-Basis
  - shadcn/ui Komponenten (Radix-basiert) fuer Buttons, Inputs, Selects, Tabs, Dialog, Tables
- Wiederverwendbare App-Komponenten eingefuehrt:
  - `PageHeader`
  - `SectionCard`
  - `DataTable`
  - `EmptyState`
  - `LoadingSkeleton`
  - `ConfirmDialog`
- UX-States pro Kernansicht ausgebaut:
  - Loading (Skeleton)
  - Empty
  - Error (mit Retry)
  - Success-Banner nach Upload/Refresh
- Seitenstruktur:
  - `/brain`: globaler Brain-Chat als zentraler Startscreen
  - `/projects`: Upload + Workspace-Kacheln fuer `Bestand` und `Geplant`
  - `/projects/[projectName]`: Projekt-KPIs + Upload + fokussierter Projekt-Chat
  - `/workspace`: Legacy-Redirect auf `/brain`

#### Graph Foundation (Neo4j)
- Optionale Neo4j-Foundation eingebaut:
  - Aktivierung via ENV (`GRAPH_ENABLED`, `NEO4J_*`)
  - Safe fallback: Backend bleibt lauffaehig, wenn Neo4j nicht installiert oder nicht aktiv ist
  - Schema-Initialisierung fuer:
    - `Scope`
    - `Project`
    - `Document`
    - `Chunk`
- Neuer Knowledge-Status-Endpunkt:
  - `GET /system/knowledge-status`
  - liefert Status fuer Metadata DB, Vector-Indizes und Neo4j-Graph
- Uploads schreiben jetzt zusaetzlich Scope-/Projekt-/Dokument-/Chunk-Knoten in den Graphen, sofern Graph aktiviert ist
- Grundlage fuer spaetere:
  - Entity-/Relationship-Extraktion
  - Graph-augmentierten Global Brain Chat
  - Excel-/Analyse-Adapter mit strukturierten Outputs

#### Graph Knowledge Extraction + Chat Augmentation
- Uploads extrahieren jetzt optional strukturierte Graph-Kandidaten pro Chunk:
  - `Entity`
  - `RELATES_TO`
  - `MENTIONED_IN`
- Extraktion laeuft konservativ ueber LLM-Structured-Output mit Fallback:
  - wenn OpenAI oder Neo4j fehlen, bleibt nur die Dokument-/Chunk-Struktur im Graph
  - Konfigurierbar ueber:
    - `GRAPH_ENTITY_EXTRACTION_ENABLED`
    - `GRAPH_ENTITY_EXTRACTION_MAX_CHUNKS`
- `POST /chat` kann jetzt zusaetzliche `graph_facts` zur Antwort zurueckgeben:
  - query-relevante Entities
  - query-relevante Beziehungen
  - aktuell zusaetzlich zum bestehenden Dokument-RAG, nicht statt dessen

#### Upload-Pipeline (`POST /upload`)
- Nimmt FormData:
  - `files[]`
  - `scope_type` (`project` | `domain` | `global`)
  - `scope_id` (Pflicht fuer `project`/`domain`, optional fuer `global`)
  - `document_type` (default `general`)
  - `project_name` (backward-compatible Alias fuer `scope_id` bei `scope_type=project`)
  - `project_type` (optional, fuer `scope_type=project`)
- Speichert Dateien:
  - `project` scope unter `backend/projects/<scope_id>/files/`
  - `domain/global` scope unter `backend/scopes/<scope_type>/<scope_id>/files/`
- Extrahiert Text:
  - PDF via `PyPDFLoader`
  - DOCX via `python-docx`
  - XLSX via `openpyxl`
  - PPTX via `python-pptx`
  - TXT/MD via Plain-Text Read
  - CSV via `csv` parser
- Speichert Text-Backup analog unter `.../text/`
- Chunkt mit `RecursiveCharacterTextSplitter`:
  - `chunk_size=1000`
  - `chunk_overlap=100`
  - Vergibt pro Chunk stabile Metadaten:
    - `chunk_id`
    - `chunk_index`
    - `chunk_position`
- `project` scope:
  - Indexiert Chunks in Projekt-Tabelle
  - Spiegelt zusaetzlich in `realestate_global`
  - Spiegelt zusaetzlich in `global_brain`
- `domain/global` scope:
  - Indexiert Chunks in `global_brain`
- Schreibt/Aktualisiert Projekt-Metadaten in `backend/projects/_registry.json`
- Schreibt Upload- und Dateimetadaten in SQL Metadata DB (`projects`, `documents`)
- Schreibt optional Dokument- und Chunk-Struktur zusaetzlich in Neo4j
- Chunk-Metadaten aktuell:
  - `source` (Dateiname)
  - `project_name`
  - `project_type`
  - `scope_type`
  - `scope_id`
  - `document_type`
  - `chunk_id`
  - `chunk_index`

#### Chat-RAG (`POST /chat`)
- Request:
  - `query` (string)
  - `scope` (`project` | `realestate_global` | `global`, default `project`)
  - `project_name` (string, Pflicht wenn `scope=project`)
  - `top_k` (optional, default `4`, valid `1..10`)
  - Optionale Filter:
    - `scope_type_filter`
    - `scope_id_filter`
    - `document_type_filter`
- Verhalten:
  - Scope `project`: nutzt projektspezifischen VectorStore
  - Scope `realestate_global`: nutzt shared Tabelle `realestate_global`
  - Scope `global`: nutzt primaer shared Tabelle `global_brain`
  - Fallback: falls shared Tabelle noch nicht vorhanden ist, Fanout-Retrieval ueber alle Projekt-Tabellen
  - Bei unbekanntem Projekt oder fehlenden Daten: HTTP `404`
  - Retrieval mit `top_k` (bevorzugt mit Relevance Scores, sonst Fallback ohne Score)
  - Antwortgenerierung via LCEL + `gpt-4o-mini`
- Response:
  - `answer`
  - `scope`
  - `effective_scope`
  - `filters_applied`
  - `sources` (dedupliziert, stabile Reihenfolge)
  - `evidence[]` mit:
    - `source`
    - `file_name`
    - `project_name`
    - `project_type`
    - `scope_type`
    - `scope_id`
    - `document_type`
    - `excerpt` (max 400 Zeichen)
    - `chunk_id` (falls in Metadaten vorhanden, sonst `null`)
    - `score` (falls verfuegbar, sonst `null`)
  - optional `graph_facts[]` mit:
    - `kind` (`entity` | `relationship`)
    - `label`
    - `text`

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
  - Shared Global-Index `global_brain`
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
  - Scope-Felder: `scope_type`, `scope_id`, `document_type`
  - Graph-Statusfelder fuer Dokumente: `graph_status`, `graph_last_indexed_at`, `graph_error_message`
- `backend/services/graph_db.py`
  - Optionale Neo4j-Verbindung, Constraint-Bootstrap und Graph-Status
- `backend/services/graph_ingest.py`
  - Scope-/Projekt-/Dokument-/Chunk-Upserts nach Neo4j
  - Entity-/Relationship-Ingestion pro Chunk (gedeckelt)
- `backend/services/graph_extraction.py`
  - strukturierte Entity-/Relationship-Extraktion fuer Chunks
- `backend/services/graph_queries.py`
  - query-relevante Graph-Fakten fuer Chat-Scope-Abfragen
- `backend/services/system_status.py`
  - Aggregiert Metadata-, Vector- und Graph-Status fuer das Frontend
- `backend/services/analysis_schema.py`
  - Strukturierte Analyse-Result-Modelle als Grundlage fuer spaetere Excel-/Template-Adapter
- `docs/LOCAL_NEO4J.md`
  - lokales Setup fuer Neo4j via Docker Compose
- `scripts/start_local_graph.ps1`
  - startet lokalen Neo4j-Container mit Backend-ENV
- `scripts/stop_local_graph.ps1`
  - stoppt lokalen Neo4j-Container
- `backend/utils/extract_file.py`
  - Dateiextraktion (PDF, DOCX, XLSX, PPTX, TXT, MD, CSV)
- `backend/utils/text_splitter.py`
  - Text zu `Document`-Chunks inkl. `chunk_id`-Vergabe
- `backend/utils/embeddings.py`
  - OpenAI Embeddings Initialisierung
- `frontend/app/*`
  - UI-Routing fuer Brain, Projects, Project Detail und Workspace-Alias
  - App Shell (Sidebar/Topbar) ueber `layout.tsx`
- `frontend/components/ui/*`
  - shadcn/ui Basiskomponenten
- `frontend/components/app/*`
  - wiederverwendbare app-spezifische Layout- und State-Komponenten
- `frontend/components/UploadForm.tsx`
  - Upload-Flow fuer `project/domain/global` inkl. `document_type`
- `frontend/components/ScopeChatPanel.tsx`
  - Scope-Chat UI fuer `project`, `realestate_global`, `global` inkl. Hero-Variante fuer Brain
- `frontend/components/BrainDashboard.tsx`
  - zentraler Global-Brain-Screen mit Knowledge-Layer-Status
- `frontend/lib/api.ts`
  - API-Client fuer FastAPI-Endpoints

### 2.3 Aktuelle API-Contracts

#### `POST /upload`
- Input: FormData
  - `scope_type`: `project` | `domain` | `global`
  - `scope_id`: string (Pflicht fuer `project/domain`)
  - `document_type`: string (optional, default `general`)
  - `project_name`: optional Alias fuer `scope_id` bei `scope_type=project`
  - `project_type`: optional, `bestand` | `geplant` (relevant fuer `project` scope)
    - `potenziell` wird aus Kompatibilitaetsgruenden weiterhin akzeptiert und intern zu `geplant` normalisiert
  - `files`: 1..n Dateien
- Erfolgsantwort:
  - `message`
  - `project_name`
  - `project_type`
  - `scope_type`
  - `scope_id`
  - `document_type`
  - `chunks_created`
- Fehler:
  - `422` bei unsupported Dateityp
  - `422` bei leerer/fehlgeschlagener Extraktion
  - `422` bei Parserfehlern (z. B. defektes/verschluesseltes PDF) mit konkreter Fehlermeldung

#### `POST /chat`
- Input: JSON
```json
{
  "scope": "project",
  "project_name": "TestProject",
  "scope_type_filter": "project",
  "scope_id_filter": "TestProject",
  "document_type_filter": "expose",
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
  "filters_applied": {
    "scope_type": "project",
    "scope_id": "TestProject",
    "document_type": "expose"
  },
  "sources": ["TestProject/file1.pdf", "TestProject/file2.pdf"],
  "evidence": [
    {
      "source": "TestProject/file1.pdf",
      "file_name": "file1.pdf",
      "project_name": "TestProject",
      "project_type": "geplant",
      "scope_type": "project",
      "scope_id": "TestProject",
      "document_type": "expose",
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
      "project_type": "geplant",
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

#### `GET /system/knowledge-status`
- Erfolgsantwort:
```json
{
  "projects": {
    "count": 2
  },
  "metadata": {
    "project_count": 2,
    "document_count": 8,
    "graph_indexed_documents": 6
  },
  "vectorstores": {
    "realestate_global_available": true,
    "global_brain_available": true
  },
  "graph": {
    "enabled": true,
    "package_available": true,
    "configured": true,
    "active": true,
    "connected": true,
    "database": "neo4j",
    "uri": "bolt://localhost:7687",
    "node_count": 124,
    "entity_count": 42,
    "relationship_count": 18
  }
}
```

### 2.4 MVP-Readiness (kurz)
Bereits vorhanden:
- Projektbezogener Upload + persistente Vektorindexierung
- Projektbezogener Chat mit nachvollziehbarer Evidenz
- Frontend-MVP mit `Brain` + `Projects`, App Shell, Design System und konsistenten UX-States
- Metadata-DB-Layer fuer Projekte und Upload-Dokumente (SQLAlchemy)
- Neo4j-Foundation fuer spaetere Graph-Augmentation im Global Brain

Noch offen fuer robustes MVP im Einsatz:
- Einheitliche Error-Struktur auf allen Endpunkten
- Minimales Logging/Observability
- Graph-Entity-/Relationship-Extraktion ueber Dokument-/Chunk-Struktur hinaus

---

## 3) Arbeitsregeln fuer schnelle, kontrollierte Weiterentwicklung
- Kleine, pruefbare Aenderungsschritte
- `main.py` schlank halten (keine Business-Logik)
- Keine grossen Refactors ohne explizites OK
- Nach jeder Aenderung: kurze Testanleitung (Uvicorn + Postman)
- Dieses Dokument bei jeder relevanten Aenderung aktualisieren

### 3.1 Laufzeit-Config (wichtig)
- `CORS_ALLOW_ORIGINS` kann genutzt werden, um erlaubte Frontend-Origin(s) zu steuern.
- Default fuer lokale Entwicklung: `http://localhost:3000,http://127.0.0.1:3000`

---

## 4) Verbindliche Leitlinie fuer die Zusammenarbeit
- Ziel ist ein `industry standard`, `state of the art` Projekt, das gleichzeitig fuer dich nachvollziehbar und lernbar bleibt.
- Jede relevante Aenderung wird mit kurzem `Warum` dokumentiert (Trade-off, Alternative, Entscheidung).
- Bevorzugt werden klare, wartbare Loesungen statt unnoetig komplexer "cleverer" Implementierungen.
- Architektur- und API-Entscheidungen werden konsistent gehalten und bei Aenderungen in diesem Dokument aktualisiert.
- Wenn eine Best-Practice-Loesung unnoetig kompliziert waere, wird eine pragmatische Zwischenstufe gewaehlt und als naechster Schritt markiert.
- Branch-First ist Standard: Entwicklung in `feat/*`, `fix/*`, `chore/*`, Merge nach `main` ueber PR.
- Direkte Commits auf `main` nur in klar begruendeten Ausnahmefaellen (z. B. akuter Hotfix).

