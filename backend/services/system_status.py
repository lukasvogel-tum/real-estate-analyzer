from services.graph_db import get_graph_status
from services.metadata_db import get_metadata_overview
from services.project_registry import list_projects
from services.vectorstore import get_global_brain_vectorstore, get_realestate_global_vectorstore


def get_knowledge_status() -> dict:
    metadata_overview = get_metadata_overview()
    graph_status = get_graph_status()

    return {
        "projects": {
            "count": len(list_projects()),
        },
        "metadata": metadata_overview,
        "vectorstores": {
            "realestate_global_available": get_realestate_global_vectorstore() is not None,
            "global_brain_available": get_global_brain_vectorstore() is not None,
        },
        "graph": graph_status,
    }
