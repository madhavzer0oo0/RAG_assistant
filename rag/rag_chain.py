import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage


SYSTEM_PROMPT = """You are a highly capable AI assistant with access to a knowledge base.
Answer questions accurately using ONLY the provided context. If the context doesn't contain
enough information, say so clearly. Be concise but thorough.

When relevant, reference which part of the context supports your answer.
If the user is following up on a previous question, use the conversation history for context."""


def build_llm(model=None, temperature=0.2):
    return ChatGroq(
        model=model or os.getenv("LLM_MODEL", "llama3-8b-8192"),
        api_key=os.getenv("GROQ_API_KEY"),
        temperature=temperature,
    )


def format_context(docs):
    parts = []
    for i, doc in enumerate(docs, 1):
        source = doc.metadata.get("source_name", "Unknown")
        parts.append(f"[Source {i}: {source}]\n{doc.page_content}")
    return "\n\n---\n\n".join(parts)


def format_history(chat_history, max_turns=5):
    if not chat_history:
        return ""
    recent = chat_history[-(max_turns * 2):]
    lines = []
    for msg in recent:
        role = "User" if msg["role"] == "user" else "Assistant"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines)


def build_prompt_messages(context, history_str, question):
    user_content = f"Context from knowledge base:\n{context}\n\n"
    if history_str:
        user_content += f"Previous conversation:\n{history_str}\n\n"
    user_content += f"Question: {question}\nAnswer:"

    return [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_content),
    ]


def retrieve_docs(retriever, question):
    """Retrieve relevant documents for a question."""
    return retriever.invoke(question)


def stream_response(retriever, question, chat_history=None, model=None, temperature=0.2):
    """Generator that yields {"type": ..., "data": ...} dicts for streaming."""
    docs = retrieve_docs(retriever, question)

    sources = []
    for d in docs:
        sources.append({
            "content": d.page_content[:300],
            "source_name": d.metadata.get("source_name", "Unknown"),
            "source_type": d.metadata.get("source_type", ""),
            "page": d.metadata.get("page"),
        })
    yield {"type": "sources", "data": sources}

    context = format_context(docs)
    history_str = format_history(chat_history)
    messages = build_prompt_messages(context, history_str, question)

    llm = build_llm(model=model, temperature=temperature)

    full_response = ""
    for chunk in llm.stream(messages):
        if chunk.content:
            full_response += chunk.content
            yield {"type": "token", "data": chunk.content}

    yield {"type": "done", "data": full_response}


def invoke_response(retriever, question, chat_history=None, model=None, temperature=0.2):
    """Non-streaming version — returns (answer, sources) tuple."""
    docs = retrieve_docs(retriever, question)

    sources = []
    for d in docs:
        sources.append({
            "content": d.page_content[:300],
            "source_name": d.metadata.get("source_name", "Unknown"),
            "source_type": d.metadata.get("source_type", ""),
            "page": d.metadata.get("page"),
        })

    context = format_context(docs)
    history_str = format_history(chat_history)
    messages = build_prompt_messages(context, history_str, question)

    llm = build_llm(model=model, temperature=temperature)
    response = llm.invoke(messages)

    return response.content.strip(), sources
