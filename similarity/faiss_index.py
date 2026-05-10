"""FAISS index management for cosine similarity search.

Uses normalized vectors with IndexFlatIP to implement cosine similarity.
Falls back to a NumPy index if faiss is unavailable.
"""

from __future__ import annotations

import logging
import pickle
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

try:
    import faiss  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    faiss = None

LOGGER = logging.getLogger(__name__)


@dataclass
class CosineIndex:
    vectors: np.ndarray

    @property
    def ntotal(self) -> int:
        return int(self.vectors.shape[0])

    def search(self, query: np.ndarray, top_k: int) -> Tuple[np.ndarray, np.ndarray]:
        if self.vectors.size == 0:
            scores = np.zeros((1, top_k), dtype=np.float32)
            indices = -np.ones((1, top_k), dtype=np.int64)
            return scores, indices

        query = np.asarray(query, dtype=np.float32)
        if query.ndim == 1:
            query = query.reshape(1, -1)

        query_norm = np.linalg.norm(query, axis=1, keepdims=True)
        query = query / np.clip(query_norm, 1e-12, None)
        scores = query @ self.vectors.T
        top_indices = np.argsort(scores[0])[::-1][:top_k]
        top_scores = scores[:, top_indices]

        if len(top_indices) < top_k:
            pad = top_k - len(top_indices)
            top_scores = np.pad(top_scores, ((0, 0), (0, pad)), constant_values=0.0)
            top_indices = np.pad(top_indices, (0, pad), constant_values=-1)

        return top_scores.astype(np.float32), top_indices.reshape(1, -1).astype(np.int64)


class FAISSIndex:
    def __init__(self, index_type: str = "cosine") -> None:
        self.index_type = index_type
        self.index: Optional[Any] = None
        self.metadata: Dict[str, object] = {}

    @staticmethod
    def _normalize(embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.clip(norms, 1e-12, None)

    def _build_index(self, embeddings: np.ndarray) -> Any:
        if embeddings.size == 0:
            raise RuntimeError("Cannot build an index from an empty embedding matrix")
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)
        embeddings = self._normalize(embeddings)
        if faiss is None:
            LOGGER.warning("faiss not available, using NumPy fallback index")
            return CosineIndex(vectors=embeddings)

        index = faiss.IndexFlatIP(int(embeddings.shape[1]))
        index.add(embeddings)
        return index

    def save(self, index_path: Path, metadata_path: Path) -> None:
        if self.index is None:
            raise RuntimeError("Cannot save index before building/loading it.")

        index_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_path.parent.mkdir(parents=True, exist_ok=True)

        if faiss is not None and hasattr(self.index, "ntotal") and not isinstance(self.index, CosineIndex):
            faiss.write_index(self.index, str(index_path))
        else:
            with index_path.open("wb") as file_handle:
                pickle.dump({"vectors": self.index.vectors}, file_handle)
        with metadata_path.open("wb") as file_handle:
            pickle.dump(self.metadata, file_handle)

        LOGGER.info("Saved cosine index: %s", index_path)

    def load(self, index_path: Path, metadata_path: Path) -> bool:
        if not index_path.exists() or not metadata_path.exists():
            return False

        try:
            if faiss is not None:
                try:
                    self.index = faiss.read_index(str(index_path))
                except Exception:
                    with index_path.open("rb") as file_handle:
                        payload = pickle.load(file_handle)
                    vectors = np.asarray(payload.get("vectors", []), dtype=np.float32)
                    self.index = CosineIndex(vectors=vectors)
            else:
                with index_path.open("rb") as file_handle:
                    payload = pickle.load(file_handle)
                vectors = np.asarray(payload.get("vectors", []), dtype=np.float32)
                self.index = CosineIndex(vectors=vectors)
            with metadata_path.open("rb") as file_handle:
                self.metadata = pickle.load(file_handle)
            LOGGER.info("Loaded cosine index with %s vectors", self.index.ntotal)
            return True
        except Exception as exc:
            LOGGER.warning("Failed to load cosine index: %s", exc)
            return False

    def _is_metadata_valid(self, embeddings_payload: Dict[str, object]) -> bool:
        if not self.metadata:
            return False

        image_paths = embeddings_payload.get("image_paths", [])
        brands = embeddings_payload.get("brands", [])
        categories = embeddings_payload.get("categories", [])

        if len(image_paths) != len(brands):
            return False

        if categories and len(categories) != len(image_paths):
            return False

        if int(self.metadata.get("num_images", -1)) != len(image_paths):
            return False

        if int(self.metadata.get("num_brands", -1)) != len(set(brands)):
            return False

        expected_root = str(embeddings_payload.get("dataset_root", ""))
        if expected_root and self.metadata.get("dataset_root") != expected_root:
            return False

        return True

    def load_or_build(
        self,
        embeddings_payload: Dict[str, object],
        index_path: str,
        metadata_path: str,
        force_rebuild: bool = False,
    ) -> "FAISSIndex":
        index_p = Path(index_path)
        metadata_p = Path(metadata_path)

        if not force_rebuild and self.load(index_p, metadata_p) and self._is_metadata_valid(embeddings_payload):
            return self

        embeddings = np.asarray(embeddings_payload["embeddings"], dtype=np.float32)
        self.index = self._build_index(embeddings)
        self.metadata = {
            "image_paths": embeddings_payload["image_paths"],
            "brands": embeddings_payload["brands"],
            "categories": embeddings_payload.get("categories", []),
            "dataset_root": embeddings_payload.get("dataset_root"),
            "embedding_dim": embeddings_payload.get("embedding_dim", embeddings.shape[1]),
            "index_type": "IndexFlatIP (cosine)",
            "num_images": len(embeddings_payload["image_paths"]),
            "num_brands": len(set(embeddings_payload["brands"])),
            "index_size": int(embeddings.shape[0]),
        }
        self.save(index_p, metadata_p)
        if int(self.index.ntotal) != int(embeddings.shape[0]):
            raise RuntimeError(
                f"FAISS index size mismatch: index={self.index.ntotal} embeddings={embeddings.shape[0]}"
            )
        LOGGER.info("Built cosine index with %s vectors", self.index.ntotal)
        return self


def build_index_from_embeddings(
    embeddings_path: str,
    output_index: str,
    output_metadata: str,
    index_type: str = "cosine",
) -> FAISSIndex:
    with Path(embeddings_path).open("rb") as file_handle:
        embeddings_payload = pickle.load(file_handle)

    cosine_index = FAISSIndex(index_type=index_type)
    return cosine_index.load_or_build(
        embeddings_payload=embeddings_payload,
        index_path=output_index,
        metadata_path=output_metadata,
        force_rebuild=True,
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
    base_dir = Path(__file__).resolve().parents[1]
    build_index_from_embeddings(
        embeddings_path=str(base_dir / "models" / "logo_embeddings.pkl"),
        output_index=str(base_dir / "similarity" / "faiss_index.index"),
        output_metadata=str(base_dir / "similarity" / "index_metadata.pkl"),
    )
