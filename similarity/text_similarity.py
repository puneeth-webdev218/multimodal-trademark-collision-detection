"""
Text similarity engine for brand/trademark names.
"""

from __future__ import annotations

import difflib
import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

LOGGER = logging.getLogger(__name__)


class NameSimilarityEngine:
    def __init__(
        self,
        brand_names: List[str],
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        cache_path: Optional[str] = None,
    ) -> None:
        self.brand_names = sorted(set(brand_names))
        self.model_name = model_name
        self.cache_path = Path(cache_path) if cache_path else Path(__file__).resolve().parents[1] / "models" / "name_embeddings.pkl"
        self.model = None
        self.embeddings: Optional[np.ndarray] = None
        self.backend = "string"

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.clip(norms, 1e-12, None)

    def _load_model(self):
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
        except Exception:
            self.backend = "string"
            return None

        if self.model is not None:
            return self.model

        try:
            self.model = SentenceTransformer(self.model_name)
            self.backend = "sbert"
            return self.model
        except Exception as exc:
            LOGGER.info("SentenceTransformer unavailable, falling back to string similarity: %s", exc)
            self.backend = "string"
            self.model = None
            return None

    def _compute_embeddings(self) -> np.ndarray:
        model = self._load_model()
        if model is None:
            vectors = np.zeros((len(self.brand_names), 1), dtype=np.float32)
            return vectors

        vectors = model.encode(self.brand_names, convert_to_numpy=True, show_progress_bar=False)
        vectors = np.asarray(vectors, dtype=np.float32)
        return self._normalize(vectors)

    def load_or_build(self, force_rebuild: bool = False) -> np.ndarray:
        if not force_rebuild and self.cache_path.exists():
            try:
                with self.cache_path.open("rb") as file_handle:
                    payload = pickle.load(file_handle)
                if payload.get("brand_names", []) == self.brand_names:
                    self.embeddings = np.asarray(payload["embeddings"], dtype=np.float32)
                    self.backend = str(payload.get("backend", self.backend))
                    return self.embeddings
            except Exception:
                pass

        self.embeddings = self._compute_embeddings()
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        with self.cache_path.open("wb") as file_handle:
            pickle.dump({"brand_names": self.brand_names, "embeddings": self.embeddings, "backend": self.backend}, file_handle)
        return self.embeddings

    def _string_score(self, query_name: str, brand_name: str) -> float:
        return difflib.SequenceMatcher(None, query_name.lower(), brand_name.lower()).ratio()

    def embed_query(self, name: str) -> np.ndarray:
        model = self._load_model()
        if model is None:
            return np.zeros((1,), dtype=np.float32)

        vector = model.encode([name], convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
        return self._normalize(vector)[0]

    def search_similar_names(self, query_name: str, top_k: int = 5) -> List[Dict[str, object]]:
        top_k = max(1, min(top_k, len(self.brand_names) or 1))

        if self.embeddings is None:
            self.load_or_build(force_rebuild=False)

        results: List[Dict[str, object]] = []
        if self.backend == "sbert" and self.embeddings is not None and self.embeddings.ndim == 2 and self.embeddings.shape[1] > 1:
            query_vec = self.embed_query(query_name)
            scores = np.dot(self.embeddings, query_vec)
            indices = np.argsort(scores)[::-1][:top_k]
            for rank, index in enumerate(indices, start=1):
                results.append({
                    "rank": rank,
                    "brand_name": self.brand_names[index],
                    "similarity_score": float(scores[index]),
                })
            return results

        scored = [
            (brand_name, self._string_score(query_name, brand_name))
            for brand_name in self.brand_names
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        for rank, (brand_name, score) in enumerate(scored[:top_k], start=1):
            results.append({
                "rank": rank,
                "brand_name": brand_name,
                "similarity_score": float(score),
            })
        return results
