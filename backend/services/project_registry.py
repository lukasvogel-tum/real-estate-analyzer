import json
import os
from datetime import datetime, timezone
from typing import Any

import lancedb

from services.vectorstore import DB_PATH, get_table_name

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BACKEND_DIR, "projects")
REGISTRY_PATH = os.path.join(PROJECTS_DIR, "_registry.json")
DEFAULT_PROJECT_TYPE = "potenziell"
VALID_PROJECT_TYPES = {"bestand", "potenziell"}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean_project_name(project_name: str) -> str:
    cleaned = (project_name or "").strip()
    if not cleaned:
        raise ValueError("Project name is required.")
    return cleaned


def normalize_project_type(project_type: str | None) -> str | None:
    if project_type is None:
        return None

    normalized = project_type.strip().lower()
    if normalized not in VALID_PROJECT_TYPES:
        valid = ", ".join(sorted(VALID_PROJECT_TYPES))
        raise ValueError(f"Invalid project_type '{project_type}'. Allowed values: {valid}.")

    return normalized


def _ensure_registry_file() -> None:
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    if not os.path.exists(REGISTRY_PATH):
        _write_registry({"projects": {}})


def _read_registry() -> dict[str, Any]:
    _ensure_registry_file()
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {"projects": {}}

    projects = data.get("projects")
    if not isinstance(projects, dict):
        return {"projects": {}}

    return {"projects": projects}


def _write_registry(data: dict[str, Any]) -> None:
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    temp_path = f"{REGISTRY_PATH}.tmp"
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
    os.replace(temp_path, REGISTRY_PATH)


def _connect_db():
    try:
        return lancedb.connect(DB_PATH)
    except Exception:
        return None


def _get_table_names(db) -> set[str]:
    if db is None:
        return set()

    try:
        response = db.list_tables()
        tables = getattr(response, "tables", None)
        if tables is not None:
            return set(tables)
    except Exception:
        pass

    try:
        return set(db.table_names())
    except Exception:
        return set()


def _count_files(path: str) -> int:
    if not os.path.isdir(path):
        return 0
    return sum(1 for entry in os.scandir(path) if entry.is_file())


def _discover_project_names(table_names: set[str]) -> set[str]:
    discovered = set()
    if os.path.isdir(PROJECTS_DIR):
        for entry in os.scandir(PROJECTS_DIR):
            if entry.is_dir():
                discovered.add(entry.name)
    return discovered.union(table_names)


def _base_project_entry(project_name: str, now_iso: str) -> dict[str, Any]:
    return {
        "project_name": project_name,
        "project_type": DEFAULT_PROJECT_TYPE,
        "created_at": now_iso,
        "updated_at": now_iso,
    }


def _build_project_info(project_name: str, entry: dict[str, Any], db, table_names: set[str]) -> dict[str, Any]:
    project_path = os.path.join(PROJECTS_DIR, project_name)
    files_path = os.path.join(project_path, "files")
    text_path = os.path.join(project_path, "text")
    table_name = get_table_name(project_name)
    has_vector_index = table_name in table_names
    chunks_indexed = 0

    if has_vector_index and db is not None:
        try:
            chunks_indexed = int(db.open_table(table_name).count_rows())
        except Exception:
            chunks_indexed = 0

    return {
        "project_name": entry.get("project_name", project_name),
        "project_type": entry.get("project_type", DEFAULT_PROJECT_TYPE),
        "created_at": entry.get("created_at"),
        "updated_at": entry.get("updated_at"),
        "files_count": _count_files(files_path),
        "text_backups_count": _count_files(text_path),
        "table_name": table_name,
        "has_vector_index": has_vector_index,
        "chunks_indexed": chunks_indexed,
    }


def _sync_registry_with_environment(registry: dict[str, Any], table_names: set[str]) -> bool:
    projects = registry["projects"]
    now_iso = _utc_now_iso()
    changed = False

    for name in _discover_project_names(table_names):
        if name not in projects:
            projects[name] = _base_project_entry(name, now_iso)
            changed = True

    for name, entry in list(projects.items()):
        if not isinstance(entry, dict):
            projects[name] = _base_project_entry(name, now_iso)
            changed = True
            continue

        if "project_name" not in entry:
            entry["project_name"] = name
            changed = True
        if "created_at" not in entry:
            entry["created_at"] = now_iso
            changed = True
        if "updated_at" not in entry:
            entry["updated_at"] = entry["created_at"]
            changed = True
        if "project_type" not in entry:
            entry["project_type"] = DEFAULT_PROJECT_TYPE
            changed = True
        else:
            try:
                normalized = normalize_project_type(entry["project_type"])
            except ValueError:
                normalized = DEFAULT_PROJECT_TYPE
            if normalized != entry["project_type"]:
                entry["project_type"] = normalized
                changed = True

    return changed


def upsert_project(project_name: str, project_type: str | None = None) -> dict[str, Any]:
    cleaned_name = _clean_project_name(project_name)
    normalized_type = normalize_project_type(project_type)
    registry = _read_registry()
    projects = registry["projects"]
    now_iso = _utc_now_iso()

    if cleaned_name not in projects or not isinstance(projects[cleaned_name], dict):
        projects[cleaned_name] = _base_project_entry(cleaned_name, now_iso)

    entry = projects[cleaned_name]
    if normalized_type is not None:
        entry["project_type"] = normalized_type
    elif not entry.get("project_type"):
        entry["project_type"] = DEFAULT_PROJECT_TYPE

    entry["project_name"] = cleaned_name
    entry.setdefault("created_at", now_iso)
    entry["updated_at"] = now_iso

    _write_registry(registry)
    project = get_project(cleaned_name)
    if project is None:
        raise RuntimeError("Failed to load project after upsert.")
    return project


def list_projects() -> list[dict[str, Any]]:
    registry = _read_registry()
    db = _connect_db()
    table_names = _get_table_names(db)
    changed = _sync_registry_with_environment(registry, table_names)
    if changed:
        _write_registry(registry)

    projects = []
    for name, entry in registry["projects"].items():
        projects.append(_build_project_info(name, entry, db, table_names))

    return sorted(projects, key=lambda item: item["project_name"].lower())


def get_project(project_name: str) -> dict[str, Any] | None:
    cleaned_name = _clean_project_name(project_name)
    projects = list_projects()
    target = cleaned_name.lower()
    for project in projects:
        if project["project_name"].lower() == target:
            return project
    return None
