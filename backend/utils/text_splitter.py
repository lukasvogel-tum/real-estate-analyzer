from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_text(texts, metadatas=None, chunk_size=1000, chunk_overlap=100):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    documents = text_splitter.create_documents(texts, metadatas=metadatas)
    return documents
