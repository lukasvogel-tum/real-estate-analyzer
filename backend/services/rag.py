from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI

DEFAULT_EXCERPT_LENGTH = 400
DEFAULT_MODEL = "gpt-4o-mini"


def _build_excerpt(text: str, max_length: int = DEFAULT_EXCERPT_LENGTH) -> str:
    clean_text = (text or "").strip()
    if len(clean_text) <= max_length:
        return clean_text
    return clean_text[:max_length].rstrip() + "..."


def _parse_score(score):
    if score is None:
        return None
    try:
        return float(score)
    except (TypeError, ValueError):
        return None


def _build_source_label(metadata: dict) -> str:
    source = metadata.get("source", "Unbekannt")
    project_name = metadata.get("project_name")
    if project_name:
        return f"{project_name}/{source}"
    return source


def retrieve_documents_with_scores(vectorstore, query: str, top_k: int):
    try:
        return vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
    except Exception:
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.invoke(query)
        return [(doc, None) for doc in docs]


def _generate_llm_answer(query: str, context: str) -> str:
    llm = ChatOpenAI(temperature=0.7, model_name=DEFAULT_MODEL)

    system_prompt = (
        "Du bist ein erfahrener Immobilien-Experte. "
        "Nutze den folgenden Kontext, um die Frage des Benutzers zu beantworten. "
        "Wenn die Antwort nicht im Kontext steht, sag das klar. "
        "\n\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )

    rag_chain = (
        {"context": lambda _x: context, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain.invoke(query)


def generate_answer_from_documents(query: str, retrieved_documents):
    """Erzeugt eine Antwort basierend auf bereits abgerufenen Treffern."""
    if not retrieved_documents:
        return {
            "answer": "Ich konnte keine relevanten Informationen in den Dokumenten finden.",
            "sources": [],
            "evidence": [],
        }

    context = "\n\n".join(doc.page_content for doc, _score in retrieved_documents)
    answer = _generate_llm_answer(query, context)

    sources = []
    seen_sources = set()
    evidence = []

    for doc, score in retrieved_documents:
        metadata = doc.metadata or {}
        source_label = _build_source_label(metadata)

        if source_label not in seen_sources:
            seen_sources.add(source_label)
            sources.append(source_label)

        evidence.append(
            {
                "source": source_label,
                "file_name": metadata.get("source", "Unbekannt"),
                "project_name": metadata.get("project_name"),
                "project_type": metadata.get("project_type"),
                "excerpt": _build_excerpt(doc.page_content),
                "chunk_id": metadata.get("chunk_id"),
                "score": _parse_score(score),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
        "evidence": evidence,
    }


def generate_answer(vectorstore, query: str, top_k: int = 4):
    """Erzeugt eine nachvollziehbare Antwort inkl. Sources und Evidence."""
    retrieved_documents = retrieve_documents_with_scores(vectorstore, query, top_k)
    return generate_answer_from_documents(query, retrieved_documents)
