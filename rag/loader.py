import os
import hashlib
from io import BytesIO

from pypdf import PdfReader
from bs4 import BeautifulSoup
import requests

from langchain_core.documents import Document

from rag.splitter import get_splitter
from rag.vectorstore import get_or_create_chroma, add_texts_to_chroma
from rag.embeddings import STEmbeddingWrapper


def get_url_hash(url: str):
    return hashlib.md5(url.encode()).hexdigest()


def clean_html_from_url(url: str):
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15).text
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "img", "nav", "header", "footer"]):
        tag.decompose()

    return soup.get_text(" ", strip=True)


def load_data(input_type, input_data):
    """Loads raw text depending on source. Returns per-page Documents with metadata."""

    if input_type == "pdf":
        if isinstance(input_data, BytesIO):
            reader = PdfReader(input_data)
        else:
            reader = PdfReader(BytesIO(input_data.read()))

        pages = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text()
            if txt:
                pages.append(Document(
                    page_content=txt,
                    metadata={"page": i + 1, "source_type": "pdf"},
                ))

        return pages, "pdf"

    if input_type == "text":
        return [Document(
            page_content=input_data,
            metadata={"source_type": "text"},
        )], "text"

    if input_type == "link":
        cleaned = clean_html_from_url(input_data)
        return [Document(
            page_content=cleaned,
            metadata={"source_type": "link", "url": input_data},
        )], "link"

    raise ValueError("Invalid input type")


def process_and_store(docs, session_id, source_name, source_type):
    """Splits documents, embeds, and appends to session's ChromaDB. Returns a retriever."""
    splitter = get_splitter()
    chunks = splitter.split_documents(docs)

    texts = [c.page_content for c in chunks]
    metadatas = [{
        **c.metadata,
        "source_name": source_name,
        "source_type": source_type,
        "chunk_index": i,
    } for i, c in enumerate(chunks)]

    embed_fn = STEmbeddingWrapper(
        os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )

    persist_path = f"vectorstore/{session_id}"
    db = get_or_create_chroma(persist_path, embed_fn)
    add_texts_to_chroma(db, texts, metadatas)

    return db.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 6, "fetch_k": 20},
    )
