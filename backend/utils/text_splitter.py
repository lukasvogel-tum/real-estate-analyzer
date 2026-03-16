from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(texts, metadatas=None, chunk_size=1000, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    documents = text_splitter.create_documents(texts, metadatas=metadatas)
    chunk_counters = {}

    for position, document in enumerate(documents):
        metadata = dict(document.metadata or {})
        source = str(metadata.get("source", "unknown")).strip() or "unknown"
        scope_type = str(metadata.get("scope_type", "project")).strip().lower() or "project"
        scope_id = str(metadata.get("scope_id", "")).strip()
        counter_key = f"{scope_type}:{scope_id}:{source}"
        chunk_index = chunk_counters.get(counter_key, 0)
        chunk_counters[counter_key] = chunk_index + 1
        metadata["chunk_index"] = chunk_index
        metadata["chunk_id"] = f"{counter_key}::chunk::{chunk_index}"
        metadata["chunk_position"] = position
        document.metadata = metadata

    return documents
