"""
Generate and cache logo embeddings for the dataset.
"""

from __future__ import annotations

import logging
import os
import pickle
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from dataset.dataset_loader import get_default_dataset_root, scan_logo_dataset
from models.feature_extractor import FeatureExtractor

LOGGER = logging.getLogger(__name__)


class EmbeddingGenerator:
    def __init__(
        self,
        dataset_root: Optional[str] = None,
        model_name: str = "auto",
        embeddings_path: Optional[str] = None,
        batch_size: int = 32,
    ) -> None:
        base_dir = Path(__file__).resolve().parents[1]
        self.dataset_root = Path(dataset_root) if dataset_root else get_default_dataset_root(base_dir)
        self.model_name = model_name
        self.batch_size = max(1, batch_size)
        self.embeddings_path = Path(embeddings_path) if embeddings_path else base_dir / "models" / "logo_embeddings.pkl"
        self.extractor = FeatureExtractor(model_name=model_name)

    def _build_payload(
        self,
        vectors: np.ndarray,
        records,
        skipped_invalid: int,
        elapsed_seconds: float,
    ) -> Dict[str, object]:
        record_payload = [
            {
                "embedding": vectors[index].astype(np.float32),
                "image_path": record.image_path,
                "category": record.category,
                "brand": record.brand,
            }
            for index, record in enumerate(records)
        ]
        image_paths = [record.image_path for record in records]
        categories = [record.category for record in records]
        brands = [record.brand for record in records]

        return {
            "embeddings": vectors.astype(np.float32),
            "records": record_payload,
            "image_paths": image_paths,
            "categories": categories,
            "brands": brands,
            "dataset_root": str(self.dataset_root.resolve()),
            "model_backend": self.extractor.backend,
            "embedding_dim": int(vectors.shape[1]) if vectors.size else int(self.extractor.embedding_dim),
            "num_images": len(image_paths),
            "num_brands": len(set(brands)),
            "num_categories": len(set(categories)),
            "skipped_invalid": skipped_invalid,
            "generated_at_epoch": time.time(),
            "generation_time_seconds": elapsed_seconds,
        }

    def load_embeddings(self) -> Optional[Dict[str, object]]:
        if not self.embeddings_path.exists():
            return None

        try:
            with self.embeddings_path.open("rb") as file_handle:
                return pickle.load(file_handle)
        except Exception as exc:
            LOGGER.warning("Failed to load cached embeddings: %s", exc)
            return None

    def _is_cache_valid(self, payload: Dict[str, object], expected_root: Path, expected_count: int) -> bool:
        try:
            if Path(str(payload.get("dataset_root", ""))).resolve() != expected_root.resolve():
                return False

            embeddings = payload.get("embeddings")
            image_paths = payload.get("image_paths", [])
            brands = payload.get("brands", [])
            categories = payload.get("categories", [])
            records = payload.get("records", [])

            if embeddings is None:
                return False

            if len(embeddings) != len(image_paths):
                return False

            if len(image_paths) != len(brands):
                return False

            if len(image_paths) != expected_count:
                return False

            if categories and len(categories) != len(image_paths):
                return False

            if records and len(records) != len(image_paths):
                return False

            if isinstance(embeddings, np.ndarray) and embeddings.ndim != 2:
                return False

            return True
        except Exception:
            return False

    def generate_embeddings(self, force_recompute: bool = False) -> Dict[str, object]:
        scan = scan_logo_dataset(str(self.dataset_root))
        records = scan["records"]
        skipped_invalid = int(scan.get("skipped_invalid", 0))
        full_dataset_num_images = len(records)

        if not records:
            raise RuntimeError(f"No valid logo images found in dataset root: {self.dataset_root}")

        if not force_recompute:
            cached = self.load_embeddings()
            if cached is not None and self._is_cache_valid(cached, self.dataset_root, len(records)):
                LOGGER.info("Using cached embeddings from %s", self.embeddings_path)
                return cached

        LOGGER.info("Generating embeddings for %s images", len(records))
        start_time = time.time()

        image_paths = [record.image_path for record in records]
        vectors, kept_paths = self.extractor.extract_batch_embeddings_with_paths(image_paths, batch_size=self.batch_size)

        if vectors.size == 0:
            raise RuntimeError("Embedding generation failed: no embeddings were produced.")

        if vectors.shape[0] != len(kept_paths):
            raise RuntimeError(
                f"Embedding generation mismatch: vectors={vectors.shape[0]} kept_paths={len(kept_paths)}"
            )

        kept_records = [record for record in records if record.image_path in kept_paths]
        if len(kept_records) != len(kept_paths):
            lookup = {record.image_path: record for record in records}
            kept_records = [lookup[path] for path in kept_paths if path in lookup]

        payload = self._build_payload(
            vectors=vectors,
            records=kept_records,
            skipped_invalid=skipped_invalid,
            elapsed_seconds=time.time() - start_time,
        )
        payload["full_dataset_num_images"] = full_dataset_num_images
        payload["indexed_num_images"] = len(kept_records)

        self.embeddings_path.parent.mkdir(parents=True, exist_ok=True)
        with self.embeddings_path.open("wb") as file_handle:
            pickle.dump(payload, file_handle)

        LOGGER.info("Saved embeddings cache to %s", self.embeddings_path)
        return payload


def load_or_generate_logo_embeddings(
    dataset_root: Optional[str] = None,
    embeddings_path: Optional[str] = None,
    model_name: str = "auto",
    force_recompute: bool = False,
    batch_size: int = 32,
) -> Dict[str, object]:
    generator = EmbeddingGenerator(
        dataset_root=dataset_root,
        embeddings_path=embeddings_path,
        model_name=model_name,
        batch_size=batch_size,
    )
    return generator.generate_embeddings(force_recompute=force_recompute)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    payload = load_or_generate_logo_embeddings()
    print(f"Images: {payload['num_images']}")
    print(f"Brands: {payload['num_brands']}")
    print(f"Categories: {payload['num_categories']}")
    print(f"Dim: {payload['embedding_dim']}")
