def split_into_chunks(text: str, chunk_size: int = 500, overlap: int = 100):
    """
    Teilt einen langen Text in kleinere, überlappende Chunks.
    Beispiel: chunk_size=500, overlap=100
    -> Chunk 1: 0–500
    -> Chunk 2: 400–900
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)

        start += chunk_size - overlap  # macht den Overlap

    return chunks

