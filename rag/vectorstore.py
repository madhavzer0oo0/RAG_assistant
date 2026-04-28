import os
from langchain_chroma import Chroma


def get_or_create_chroma(persist_path, embed_fn):
    """
    Opens an existing Chroma collection or creates a new one.
    Supports appending documents across multiple ingest calls.
    """
    os.makedirs(persist_path, exist_ok=True)
    return Chroma(
        persist_directory=persist_path,
        embedding_function=embed_fn,
    )


def add_texts_to_chroma(db, texts, metadatas=None):
    """Add new texts (with optional metadata) to an existing Chroma DB."""
    if texts:
        db.add_texts(texts=texts, metadatas=metadatas)
    return db
