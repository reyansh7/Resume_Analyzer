from typing import List
import os
import numpy as np


class EmbeddingService:
    _shared_model = None
    _shared_model_name = None

    def __init__(self, model_name: str | None = None) -> None:
        resolved_model_name = (model_name or os.getenv("MODEL_NAME") or "sentence-transformers/all-MiniLM-L6-v2").strip()
        self.model_name = resolved_model_name
        if EmbeddingService._shared_model is not None and EmbeddingService._shared_model_name == resolved_model_name:
            self.model = EmbeddingService._shared_model
            return

        self.model = None
        try:
            from sentence_transformers import SentenceTransformer

            loaded_model = SentenceTransformer(resolved_model_name)
            EmbeddingService._shared_model = loaded_model
            EmbeddingService._shared_model_name = resolved_model_name
            self.model = loaded_model
        except Exception:
            self.model = None

    def encode(self, texts: List[str]) -> np.ndarray:
        if self.model:
            return np.array(self.model.encode(texts, normalize_embeddings=True))

        vectors = []
        for text in texts:
            tokens = text.lower().split()
            vec = np.zeros(128)
            for token in tokens:
                vec[hash(token) % 128] += 1
            norm = np.linalg.norm(vec)
            vectors.append(vec / norm if norm > 0 else vec)
        return np.array(vectors)
