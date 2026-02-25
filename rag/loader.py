import os
import hashlib
from io import BytesIO
from pypdf import PdfReader
from bs4 import BeautifulSoup
import requests

from langchain_core.documents import Document

from rag.splitter import get_splitter
from rag.vectorstore import create_persistent_chroma
from rag.embeddings import STEmbeddingWrapper


def get_url_hash(url: str):
    return hashlib.md5(url.encode()).hexdigest()


def clean_html_from_url(url: str):
    html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "img", "nav", "header", "footer"]):
        tag.decompose()

    return soup.get_text(" ", strip=True)


def load_data(input_type, input_data):
    """Loads raw text depending on source."""

    if input_type == "pdf":
        if isinstance(input_data, BytesIO):
            reader = PdfReader(input_data)
        else:
            reader = PdfReader(BytesIO(input_data.read()))

        text = ""
        for page in reader.pages:
            txt = page.extract_text()
            if txt:
                text += txt

        return [Document(page_content=text)], "pdf"

    if input_type == "text":
        return [Document(page_content=input_data)], "text"

    if input_type == "link":
        cleaned = clean_html_from_url(input_data)
        return [Document(page_content=cleaned)], "link"

    raise ValueError("Invalid input type")


def process_and_store(docs, doc_type, input_source):
    """Splits documents, embeds, and stores in ChromaDB. Returns a retriever."""
    splitter = get_splitter()
    chunks = splitter.split_documents(docs)
    text_chunks = [c.page_content for c in chunks]

    # Use the same local STEmbeddingWrapper for ALL doc types (no Ollama needed)
    embed_fn = STEmbeddingWrapper(
        os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )

    if doc_type in ["pdf", "text"]:
        persist_path = f"vectorstore/{doc_type}"
    elif doc_type == "link":
        url_hash = get_url_hash(input_source)
        persist_path = f"vectorstore/web/{url_hash}"
    else:
        raise ValueError(f"Unknown doc type: {doc_type}")

    db = create_persistent_chroma(text_chunks, embed_fn, persist_path)
    return db.as_retriever()
