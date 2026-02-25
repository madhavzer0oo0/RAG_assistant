import os
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel


def build_rag_chain(retriever):
    llm = ChatGroq(
        model=os.getenv("LLM_MODEL", "llama3-8b-8192"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=0.2,
    )

    prompt = ChatPromptTemplate.from_template("""
You are a helpful AI assistant.
Answer the question using ONLY the context below.
If the answer is not found, say: "I'm not sure based on the provided context."

Context:
{context}

Question: {question}

Answer:
""")

    chain = (
        RunnableParallel({
            "context": retriever,
            "question": RunnablePassthrough()
        })
        | prompt
        | llm
    )

    return chain
