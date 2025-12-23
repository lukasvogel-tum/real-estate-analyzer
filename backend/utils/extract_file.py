from langchain_community.document_loaders import PyPDFLoader


def extract_text_from_file(file_path):
    if file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        pages = loader.load_and_split()
        return " ".join([page.page_content for page in pages])
    # Add more file types here
    else:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
