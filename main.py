import os
from io import BytesIO
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.loader import load_data, process_and_store
from rag.rag_chain import build_rag_chain

load_dotenv()

app = FastAPI(
    title="RAG Q&A API",
    description="Retrieval-Augmented Generation API — supports PDF, URL, and plain text.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory retriever store keyed by a session/source id
_retrievers: dict = {}


# ── Request / Response Models ──────────────────────────────────────────────────

class TextIngestRequest(BaseModel):
    content: str          # raw text
    session_id: str = "default"

class LinkIngestRequest(BaseModel):
    url: str
    session_id: str = "default"

class QueryRequest(BaseModel):
    question: str
    session_id: str = "default"

class IngestResponse(BaseModel):
    message: str
    session_id: str

class QueryResponse(BaseModel):
    answer: str
    session_id: str


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "RAG Q&A API is running."}

@app.get("/health")
def health():
    return {"status": "ok", "active_sessions": list(_retrievers.keys())}


# ── Ingest Endpoints ───────────────────────────────────────────────────────────

@app.post("/ingest/pdf", response_model=IngestResponse)
async def ingest_pdf(
    file: UploadFile = File(...),
    session_id: str = "default",
):
    """Upload a PDF and index it."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        contents = await file.read()
        docs, doc_type = load_data("pdf", BytesIO(contents))
        retriever = process_and_store(docs, doc_type, file.filename)
        _retrievers[session_id] = retriever
        return IngestResponse(message="PDF indexed successfully.", session_id=session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/link", response_model=IngestResponse)
def ingest_link(request: LinkIngestRequest):
    """Scrape a URL and index its content."""
    try:
        docs, doc_type = load_data("link", request.url)
        retriever = process_and_store(docs, doc_type, request.url)
        _retrievers[request.session_id] = retriever
        return IngestResponse(message="URL indexed successfully.", session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingest/text", response_model=IngestResponse)
def ingest_text(request: TextIngestRequest):
    """Index raw text content."""
    try:
        docs, doc_type = load_data("text", request.content)
        retriever = process_and_store(docs, doc_type, "text_input")
        _retrievers[request.session_id] = retriever
        return IngestResponse(message="Text indexed successfully.", session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Query Endpoint ─────────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """Ask a question against previously indexed content."""
    retriever = _retrievers.get(request.session_id)
    if not retriever:
        raise HTTPException(
            status_code=404,
            detail=f"No indexed data found for session '{request.session_id}'. Call an /ingest/* endpoint first.",
        )
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        chain = build_rag_chain(retriever)
        response = chain.invoke(request.question)
        return QueryResponse(answer=response.content.strip(), session_id=request.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
