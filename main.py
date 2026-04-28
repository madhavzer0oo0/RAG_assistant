import os
import json
from io import BytesIO
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag.loader import load_data, process_and_store
from rag.rag_chain import stream_response, invoke_response

load_dotenv()

app = FastAPI(
    title="RAG Q&A API",
    description="Advanced Retrieval-Augmented Generation API — supports PDF, URL, text, streaming, memory, and source citations.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Session Store ──────────────────────────────────────────────────────────────

@dataclass
class SessionData:
    retriever: Any = None
    chat_history: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "llama3-8b-8192"))
    temperature: float = 0.2
    top_k: int = 6
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


_sessions: dict[str, SessionData] = {}


def _get_or_create_session(session_id: str) -> SessionData:
    if session_id not in _sessions:
        _sessions[session_id] = SessionData()
    return _sessions[session_id]


# ── Request / Response Models ──────────────────────────────────────────────────

class TextIngestRequest(BaseModel):
    content: str
    session_id: str = "default"

class LinkIngestRequest(BaseModel):
    url: str
    session_id: str = "default"

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"

class ConfigRequest(BaseModel):
    session_id: str = "default"
    model: Optional[str] = None
    temperature: Optional[float] = None
    top_k: Optional[int] = None

class IngestResponse(BaseModel):
    message: str
    session_id: str
    source_count: int = 0

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    sources: list = []

class SourceInfo(BaseModel):
    name: str
    type: str
    ingested_at: str


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "RAG Q&A API v2.0 is running.", "version": "2.0.0"}

@app.get("/health")
def health():
    return {
        "status": "ok",
        "active_sessions": list(_sessions.keys()),
        "session_count": len(_sessions),
    }


# ── Ingest Endpoints ───────────────────────────────────────────────────────────

@app.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    session_id: str = "default",
):
    """Upload a PDF and add it to the session's knowledge base."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        contents = await file.read()
        docs, doc_type = load_data("pdf", BytesIO(contents))
        session = _get_or_create_session(session_id)
        session.retriever = process_and_store(docs, session_id, file.filename, doc_type)
        session.sources.append({
            "name": file.filename,
            "type": "pdf",
            "ingested_at": datetime.utcnow().isoformat(),
        })
        return IngestResponse(
            message=f"PDF '{file.filename}' indexed successfully.",
            session_id=session_id,
            source_count=len(session.sources),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/link", response_model=IngestResponse)
def ingest_link(request: LinkIngestRequest):
    """Scrape a URL and add it to the session's knowledge base."""
    try:
        docs, doc_type = load_data("link", request.url)
        session = _get_or_create_session(request.session_id)
        session.retriever = process_and_store(docs, request.session_id, request.url, doc_type)
        session.sources.append({
            "name": request.url,
            "type": "link",
            "ingested_at": datetime.utcnow().isoformat(),
        })
        return IngestResponse(
            message="URL indexed successfully.",
            session_id=request.session_id,
            source_count=len(session.sources),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/text", response_model=IngestResponse)
def ingest_text(request: TextIngestRequest):
    """Index raw text content into the session's knowledge base."""
    try:
        docs, doc_type = load_data("text", request.content)
        session = _get_or_create_session(request.session_id)
        session.retriever = process_and_store(docs, request.session_id, "text_input", doc_type)
        session.sources.append({
            "name": f"Text snippet ({len(request.content)} chars)",
            "type": "text",
            "ingested_at": datetime.utcnow().isoformat(),
        })
        return IngestResponse(
            message="Text indexed successfully.",
            session_id=request.session_id,
            source_count=len(session.sources),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Query Endpoints ────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """Ask a question (non-streaming). Returns answer + source citations."""
    session = _sessions.get(request.session_id)
    if not session or not session.retriever:
        raise HTTPException(
            status_code=404,
            detail=f"No indexed data for session '{request.session_id}'.",
        )
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        answer, sources = invoke_response(
            session.retriever,
            request.question,
            chat_history=session.chat_history,
            model=session.model,
            temperature=session.temperature,
        )
        session.chat_history.append({"role": "user", "content": request.question})
        session.chat_history.append({"role": "assistant", "content": answer})
        return QueryResponse(answer=answer, session_id=request.session_id, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/stream")
def query_stream(request: QueryRequest):
    """Ask a question with streaming response (NDJSON)."""
    session = _sessions.get(request.session_id)
    if not session or not session.retriever:
        raise HTTPException(
            status_code=404,
            detail=f"No indexed data for session '{request.session_id}'.",
        )
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    def generate():
        full_response = ""
        for event in stream_response(
            session.retriever,
            request.question,
            chat_history=session.chat_history,
            model=session.model,
            temperature=session.temperature,
        ):
            if event["type"] == "done":
                full_response = event["data"]
            yield json.dumps(event) + "\n"

        session.chat_history.append({"role": "user", "content": request.question})
        session.chat_history.append({"role": "assistant", "content": full_response})

    return StreamingResponse(generate(), media_type="application/x-ndjson")


# ── Session Management ─────────────────────────────────────────────────────────

@app.get("/session/{session_id}/sources")
def get_session_sources(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        return {"sources": [], "session_id": session_id}
    return {"sources": session.sources, "session_id": session_id}


@app.get("/session/{session_id}/history")
def get_session_history(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        return {"history": [], "session_id": session_id}
    return {"history": session.chat_history, "session_id": session_id}


@app.post("/session/{session_id}/config")
def update_session_config(session_id: str, config: ConfigRequest):
    session = _get_or_create_session(session_id)
    if config.model is not None:
        session.model = config.model
    if config.temperature is not None:
        session.temperature = max(0.0, min(1.0, config.temperature))
    if config.top_k is not None:
        session.top_k = max(1, min(20, config.top_k))
    return {
        "session_id": session_id,
        "model": session.model,
        "temperature": session.temperature,
        "top_k": session.top_k,
    }


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]
    return {"message": f"Session '{session_id}' cleared.", "session_id": session_id}


@app.get("/session/{session_id}/export")
def export_session(session_id: str):
    """Export chat history as Markdown."""
    session = _sessions.get(session_id)
    if not session or not session.chat_history:
        raise HTTPException(status_code=404, detail="No history to export.")

    md = f"# RAG Assistant — Chat Export\n\n"
    md += f"**Session:** `{session_id}`\n"
    md += f"**Model:** {session.model}\n"
    md += f"**Sources:** {len(session.sources)}\n\n---\n\n"

    for msg in session.chat_history:
        if msg["role"] == "user":
            md += f"### 🧑 You\n{msg['content']}\n\n"
        else:
            md += f"### 🤖 Assistant\n{msg['content']}\n\n---\n\n"

    return StreamingResponse(
        iter([md]),
        media_type="text/markdown",
        headers={"Content-Disposition": f"attachment; filename=chat_{session_id[:8]}.md"},
    )


@app.get("/models")
def list_models():
    """List available Groq models."""
    return {
        "models": [
            {"id": "llama3-8b-8192", "name": "Llama 3 8B", "context": 8192},
            {"id": "llama3-70b-8192", "name": "Llama 3 70B", "context": 8192},
            {"id": "mixtral-8x7b-32768", "name": "Mixtral 8x7B", "context": 32768},
            {"id": "gemma2-9b-it", "name": "Gemma 2 9B", "context": 8192},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)