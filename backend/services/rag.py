from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def generate_answer(vectorstore, query: str):
    """Erzeugt eine Antwort basierend auf dem VectorStore und der Query."""
    
    llm = ChatOpenAI(temperature=0.7, model_name="gpt-4o-mini")
    
    system_prompt = (
        "Du bist ein erfahrener Immobilien-Experte. "
        "Nutze den folgenden Kontext, um die Frage des Benutzers zu beantworten. "
        "Wenn du die Antwort nicht weißt, sag es einfach. "
        "\n\n"
        "{context}"
    )
    
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", "{input}"),
        ]
    )
    
    retriever = vectorstore.as_retriever()
    
    # 1. Dokumente abrufen
    docs = retriever.invoke(query)
    
    if not docs:
        return {
            "answer": "Ich konnte keine relevanten Informationen in den Dokumenten finden.",
            "evidence": []
        }
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Modern LCEL RAG Chain (avoids langchain.chains)
    rag_chain = (
        {"context": lambda x: format_docs(docs), "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    answer = rag_chain.invoke(query)
    
    # Evidence strukturieren: Quelle und Textausschnitt (Chunk) zurückgeben
    evidence = []
    for doc in docs:
        text = doc.page_content.strip()
        excerpt = text[:100] + "..." if len(text) > 100 else text
        evidence.append({
            "source": doc.metadata.get("source", "Unbekannt"),
            "excerpt": excerpt
        })
    
    return {
        "answer": answer,
        "evidence": evidence
    }