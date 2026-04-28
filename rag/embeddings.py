from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer
import threading

_model_cache = {}
_lock = threading.Lock()


class STEmbeddingWrapper(Embeddings):
    """Thread-safe singleton-cached embedding wrapper."""

    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self._model_name = model_name

    @property
    def model(self):
        if self._model_name not in _model_cache:
            with _lock:
                if self._model_name not in _model_cache:
                    _model_cache[self._model_name] = SentenceTransformer(self._model_name)
        return _model_cache[self._model_name]

    def embed_documents(self, texts):
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text):
        return self.model.encode([text], show_progress_bar=False)[0].tolist()
