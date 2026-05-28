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


def _normalize_graph_facts(graph_facts: list[dict] | None) -> list[dict]:
    normalized = []
    for item in graph_facts or []:
        if not isinstance(item, dict):
            continue
        text = str(item.get("text", "")).strip()
        if not text:
            continue
        normalized.append(
            {
                "kind": str(item.get("kind", "fact")).strip() or "fact",
                "label": str(item.get("label", "")).strip() or None,
                "text": text,
            }
        )
    return normalized


def _normalize_metadata_filters(metadata_filters: dict | None) -> dict[str, str]:
    if not metadata_filters:
        return {}

    normalized = {}
    for key, value in metadata_filters.items():
        if value is None:
            continue
        cleaned = str(value).strip()
        if cleaned:
            normalized[key] = cleaned
    return normalized


def _metadata_matches_filters(metadata: dict, metadata_filters: dict[str, str]) -> bool:
    if not metadata_filters:
        return True

    for key, expected in metadata_filters.items():
        actual = metadata.get(key)
        if actual is None:
            return False
        if str(actual).strip().lower() != expected.strip().lower():
            return False
    return True


def apply_metadata_filters(retrieved_documents, metadata_filters: dict | None):
    normalized_filters = _normalize_metadata_filters(metadata_filters)
    if not normalized_filters:
        return retrieved_documents

    return [
        (doc, score)
        for doc, score in retrieved_documents
        if _metadata_matches_filters(doc.metadata or {}, normalized_filters)
    ]


def retrieve_documents_with_scores(
    vectorstore, query: str, top_k: int, metadata_filters: dict | None = None
):
    fetch_k = max(top_k, top_k * 8)
    try:
        retrieved = vectorstore.similarity_search_with_relevance_scores(query, k=fetch_k)
    except Exception:
        retriever = vectorstore.as_retriever(search_kwargs={"k": fetch_k})
        docs = retriever.invoke(query)
        retrieved = [(doc, None) for doc in docs]

    filtered = apply_metadata_filters(retrieved, metadata_filters)
    return filtered[:top_k]


def _generate_llm_answer(query: str, context: str) -> str:
    llm = ChatOpenAI(temperature=0.7, model_name=DEFAULT_MODEL)

    system_prompt = (
        "Du bist ein erfahrener Immobilien-Experte. "
        "Nutze den folgenden Kontext aus Dokumenten und optionalen Graph-Fakten, um die Frage des Benutzers zu beantworten. "
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


def generate_answer_from_documents(
    query: str,
    retrieved_documents,
    graph_context: str | None = None,
    graph_facts: list[dict] | None = None,
):
    """Erzeugt eine Antwort basierend auf bereits abgerufenen Treffern."""
    normalized_graph_facts = _normalize_graph_facts(graph_facts)

    if not retrieved_documents and not (graph_context or normalized_graph_facts):
        return {
            "answer": "Ich konnte keine relevanten Informationen in den Dokumenten finden.",
            "sources": [],
            "evidence": [],
            "graph_facts": [],
        }

    context_sections = []
    if retrieved_documents:
        context_sections.append(
            "Dokumentkontext:\n" + "\n\n".join(doc.page_content for doc, _score in retrieved_documents)
        )
    if graph_context:
        context_sections.append("Graph-Fakten:\n" + graph_context)

    context = "\n\n".join(context_sections)
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
                "scope_type": metadata.get("scope_type"),
                "scope_id": metadata.get("scope_id"),
                "document_type": metadata.get("document_type"),
                "excerpt": _build_excerpt(doc.page_content),
                "chunk_id": metadata.get("chunk_id"),
                "score": _parse_score(score),
            }
        )

    return {
        "answer": answer,
        "sources": sources,
        "evidence": evidence,
        "graph_facts": normalized_graph_facts,
    }


def generate_answer(
    vectorstore,
    query: str,
    top_k: int = 4,
    metadata_filters: dict | None = None,
    graph_context: str | None = None,
    graph_facts: list[dict] | None = None,
):
    """Erzeugt eine nachvollziehbare Antwort inkl. Sources und Evidence."""
    retrieved_documents = retrieve_documents_with_scores(
        vectorstore, query, top_k, metadata_filters=metadata_filters
    )
    return generate_answer_from_documents(
        query,
        retrieved_documents,
        graph_context=graph_context,
        graph_facts=graph_facts,
    )
