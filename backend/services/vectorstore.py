import lancedb
from langchain_community.vectorstores import LanceDB
from utils.embeddings import get_embeddings

DB_PATH = "./lancedb"

def get_table_name(project_name: str) -> str:
    """Erzeugt einen sicheren Tabellennamen aus dem Projektnamen."""
    return project_name.lower().replace(" ", "_")

def get_vectorstore(project_name: str):
    """Lädt einen existierenden VectorStore für ein Projekt."""
    db = lancedb.connect(DB_PATH)
    table_name = get_table_name(project_name)
    embeddings = get_embeddings()

    if table_name in db.table_names():
        return LanceDB(connection=db, embedding=embeddings, table_name=table_name)
    return None

def add_documents_to_project(project_name: str, documents: list):
    """Fügt Dokumente zu einem Projekt-VectorStore hinzu (oder erstellt ihn)."""
    db = lancedb.connect(DB_PATH)
    table_name = get_table_name(project_name)
    embeddings = get_embeddings()

    if table_name in db.table_names():
        # Tabelle existiert -> öffnen und hinzufügen
        vectorstore = LanceDB(connection=db, embedding=embeddings, table_name=table_name)
        try:
            vectorstore.add_documents(documents)
        except ValueError as e:
            # Fix für Schema-Konflikte (z.B. wenn 'source' neu hinzukommt)
            if "not found in target schema" in str(e):
                db.drop_table(table_name)
                LanceDB.from_documents(documents, embeddings, connection=db, table_name=table_name)
            else:
                raise e
    else:
        # Tabelle existiert nicht -> neu erstellen mit Dokumenten
        LanceDB.from_documents(documents, embeddings, connection=db, table_name=table_name)