from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

DEFAULT_EXCERPT_LENGTH = 400


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


def _retrieve_documents_with_scores(vectorstore, query: str, top_k: int):
    try:
        return vectorstore.similarity_search_with_relevance_scores(query, k=top_k)
    except Exception:
        retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})
        docs = retriever.invoke(query)
        return [(doc, None) for doc in docs]


def generate_answer(vectorstore, query: str, top_k: int = 4):
    """Erzeugt eine nachvollziehbare Antwort inkl. Sources und Evidence."""

    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o-mini")

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

    retrieved_documents = _retrieve_documents_with_scores(vectorstore, query, top_k)
    if not retrieved_documents:
        return {
            "answer": "Ich konnte keine relevanten Informationen in den Dokumenten finden.",
            "sources": [],
            "evidence": [],
        }

    docs = [doc for doc, _score in retrieved_documents]
    context = "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": lambda _x: context, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = rag_chain.invoke(query)

    sources = []
    seen_sources = set()
    evidence = []

    for doc, score in retrieved_documents:
        metadata = doc.metadata or {}
        source = metadata.get("source", "Unbekannt")

        if source not in seen_sources:
            seen_sources.add(source)
            sources.append(source)

        evidence.append(
            {
                "source": source,
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
