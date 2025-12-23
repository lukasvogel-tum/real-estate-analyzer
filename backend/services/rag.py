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
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Modern LCEL RAG Chain (avoids langchain.chains)
    rag_chain = (
        {"context": retriever | format_docs, "input": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain.invoke(query)