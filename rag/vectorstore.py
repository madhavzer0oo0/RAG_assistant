import os
from langchain_chroma import Chroma


def create_persistent_chroma(text_chunks, embed_fn, persist_path):
    """
    Creates or loads a Chroma vector DB stored on disk.
    Saves embeddings for reuse.
    """
    os.makedirs(persist_path, exist_ok=True)

    db = Chroma.from_texts(
        texts=text_chunks,
        embedding=embed_fn,
        persist_directory=persist_path,
    )
    # Note: persist() is no longer needed in langchain-chroma >= 0.1.0
    # Data is automatically persisted when persist_directory is set.

    return db
