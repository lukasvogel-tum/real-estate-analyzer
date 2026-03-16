import os
from typing import Any

try:
    from neo4j import GraphDatabase
except ImportError:  # pragma: no cover - graceful fallback without optional dependency
    GraphDatabase = None


_driver = None
_driver_config: tuple[str, str, str, str] | None = None


def _env_bool(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).strip().lower() in {"1", "true", "yes", "on"}


def get_graph_settings() -> dict[str, str | bool]:
    return {
        "enabled": _env_bool("GRAPH_ENABLED", "false"),
        "uri": os.getenv("NEO4J_URI", "").strip(),
        "username": os.getenv("NEO4J_USERNAME", "").strip(),
        "password": os.getenv("NEO4J_PASSWORD", "").strip(),
        "database": os.getenv("NEO4J_DATABASE", "neo4j").strip() or "neo4j",
    }


def graph_package_available() -> bool:
    return GraphDatabase is not None


def graph_is_configured() -> bool:
    settings = get_graph_settings()
    return bool(settings["uri"] and settings["username"] and settings["password"])


def graph_is_enabled() -> bool:
    settings = get_graph_settings()
    return bool(settings["enabled"]) and graph_package_available() and graph_is_configured()


def get_graph_database() -> str:
    return str(get_graph_settings()["database"])


def get_graph_driver():
    global _driver, _driver_config
    if not graph_is_enabled():
        return None

    settings = get_graph_settings()
    current_config = (
        str(settings["uri"]),
        str(settings["username"]),
        str(settings["password"]),
        str(settings["database"]),
    )
    if _driver is not None and _driver_config != current_config:
        close_graph_driver()

    if _driver is None:
        _driver = GraphDatabase.driver(
            str(settings["uri"]),
            auth=(str(settings["username"]), str(settings["password"])),
        )
        _driver_config = current_config

    return _driver


def close_graph_driver() -> None:
    global _driver, _driver_config
    if _driver is not None:
        _driver.close()
    _driver = None
    _driver_config = None


def execute_cypher(query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    driver = get_graph_driver()
    if driver is None:
        return []

    with driver.session(database=get_graph_database()) as session:
        result = session.run(query, parameters or {})
        return [record.data() for record in result]


def init_graph() -> None:
    if not graph_is_enabled():
        return

    constraints = [
        "CREATE CONSTRAINT scope_key_unique IF NOT EXISTS FOR (s:Scope) REQUIRE s.scope_key IS UNIQUE",
        "CREATE CONSTRAINT project_name_unique IF NOT EXISTS FOR (p:Project) REQUIRE p.project_name IS UNIQUE",
        "CREATE CONSTRAINT document_key_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.document_key IS UNIQUE",
        "CREATE CONSTRAINT chunk_id_unique IF NOT EXISTS FOR (c:Chunk) REQUIRE c.chunk_id IS UNIQUE",
        "CREATE CONSTRAINT entity_key_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_key IS UNIQUE",
    ]

    driver = get_graph_driver()
    if driver is None:
        return

    try:
        with driver.session(database=get_graph_database()) as session:
            for constraint in constraints:
                session.run(constraint)
    except Exception:
        close_graph_driver()


def ping_graph() -> bool:
    driver = get_graph_driver()
    if driver is None:
        return False

    try:
        with driver.session(database=get_graph_database()) as session:
            session.run("RETURN 1 AS ok").single()
        return True
    except Exception:
        return False


def get_graph_status() -> dict[str, Any]:
    settings = get_graph_settings()
    connected = ping_graph() if graph_is_enabled() else False

    node_count = 0
    entity_count = 0
    relationship_count = 0
    if connected:
        try:
            result = execute_cypher("MATCH (n) RETURN count(n) AS node_count")
            node_count = int(result[0]["node_count"]) if result else 0
        except Exception:
            node_count = 0
        try:
            result = execute_cypher("MATCH (e:Entity) RETURN count(e) AS entity_count")
            entity_count = int(result[0]["entity_count"]) if result else 0
        except Exception:
            entity_count = 0
        try:
            result = execute_cypher("MATCH ()-[r:RELATES_TO]->() RETURN count(r) AS relationship_count")
            relationship_count = int(result[0]["relationship_count"]) if result else 0
        except Exception:
            relationship_count = 0

    return {
        "enabled": bool(settings["enabled"]),
        "package_available": graph_package_available(),
        "configured": graph_is_configured(),
        "active": graph_is_enabled(),
        "connected": connected,
        "database": str(settings["database"]),
        "uri": str(settings["uri"]) or None,
        "node_count": node_count,
        "entity_count": entity_count,
        "relationship_count": relationship_count,
    }
