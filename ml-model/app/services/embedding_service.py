from typing import List
import numpy as np


class EmbeddingService:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model = None
        self.model_name = model_name
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
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
