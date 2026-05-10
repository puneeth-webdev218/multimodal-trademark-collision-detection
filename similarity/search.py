"""Unified trademark similarity search using precomputed artifacts only."""

from __future__ import annotations

import logging
import pickle
import random
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote

import numpy as np

from models.feature_extractor import FeatureExtractor
from similarity.faiss_index import FAISSIndex
from similarity.text_similarity import NameSimilarityEngine

LOGGER = logging.getLogger(__name__)


class SimilaritySearch:
    def __init__(
        self,
        dataset_root: Optional[str] = None,
        embeddings_path: Optional[str] = None,
        index_path: Optional[str] = None,
        metadata_path: Optional[str] = None,
        name_embeddings_path: Optional[str] = None,
        model_name: str = "auto",
        top_k_default: int = 5,
    ) -> None:
        base = Path(__file__).resolve().parents[1]
        self.dataset_root = dataset_root or str(base / "dataset" / "subset")
        self.embeddings_path = Path(embeddings_path) if embeddings_path else base / "models" / "logo_embeddings.pkl"
        self.index_path = Path(index_path) if index_path else base / "similarity" / "faiss_index.index"
        self.metadata_path = Path(metadata_path) if metadata_path else base / "similarity" / "index_metadata.pkl"
        self.name_embeddings_path = Path(name_embeddings_path) if name_embeddings_path else base / "models" / "name_embeddings.pkl"
        self.model_name = model_name
        self.top_k_default = top_k_default

        self.feature_extractor = FeatureExtractor(model_name=model_name)
        self.faiss_index = FAISSIndex(index_type="cosine")
        self.embeddings_payload: Optional[Dict[str, object]] = None
        self.name_engine: Optional[NameSimilarityEngine] = None
        self._initialized = False

    def _load_precomputed_embeddings(self) -> Dict[str, object]:
        if not self.embeddings_path.exists():
            raise FileNotFoundError(
                f"Embeddings file not found: {self.embeddings_path}. Run prebuild_index.py first."
            )
        with self.embeddings_path.open("rb") as file_handle:
            payload = pickle.load(file_handle)

        required_keys = {"embeddings", "image_paths", "brands"}
        missing = [key for key in required_keys if key not in payload]
        if missing:
            raise RuntimeError(f"Embeddings payload is missing keys: {missing}")

        return payload

    def _ensure_loaded(self) -> None:
        if self._initialized:
            return

        start_time = time.time()
        LOGGER.info("Loading trademark similarity engine")

        self.embeddings_payload = self._load_precomputed_embeddings()

        LOGGER.info(
            "Loaded precomputed embeddings: %s images, %s brands, %s categories",
            self.embeddings_payload.get("num_images"),
            self.embeddings_payload.get("num_brands"),
            self.embeddings_payload.get("num_categories"),
        )

        if not self.faiss_index.load(self.index_path, self.metadata_path):
            raise FileNotFoundError(
                f"FAISS artifacts missing or invalid: index={self.index_path}, metadata={self.metadata_path}. "
                "Run prebuild_index.py first."
            )

        assert self.faiss_index.index is not None
        if int(self.faiss_index.index.ntotal) <= 0:
            raise RuntimeError("FAISS index loaded with zero vectors.")

        metadata_paths = list(self.faiss_index.metadata.get("image_paths", []))
        if not metadata_paths:
            self.faiss_index.metadata["image_paths"] = list(self.embeddings_payload.get("image_paths", []))
            self.faiss_index.metadata["brands"] = list(self.embeddings_payload.get("brands", []))
            self.faiss_index.metadata["categories"] = list(self.embeddings_payload.get("categories", []))

        expected = len(self.faiss_index.metadata.get("image_paths", []))
        if expected != int(self.faiss_index.index.ntotal):
            raise RuntimeError(
                f"FAISS metadata mismatch: metadata image_paths={expected}, index vectors={self.faiss_index.index.ntotal}"
            )

        brands = list(dict.fromkeys(self.embeddings_payload.get("brands", [])))
        if self.name_embeddings_path.exists():
            self.name_engine = NameSimilarityEngine(brands, cache_path=str(self.name_embeddings_path))
            self.name_engine.load_or_build(force_rebuild=False)
        else:
            self.name_engine = None
            LOGGER.info("Name similarity cache not found at %s; continuing with image similarity only", self.name_embeddings_path)

        self._initialized = True
        LOGGER.info("Similarity engine initialized in %.2fs", time.time() - start_time)

    def _search_image(self, query_embedding: np.ndarray, top_k: int) -> List[Dict[str, object]]:
        assert self.faiss_index.index is not None
        assert self.faiss_index.metadata

        query = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self.faiss_index.index.search(query, top_k)

        paths = list(self.faiss_index.metadata.get("image_paths", []))
        brands = list(self.faiss_index.metadata.get("brands", []))
        categories = list(self.faiss_index.metadata.get("categories", []))

        results: List[Dict[str, object]] = []
        for rank, (score, index) in enumerate(zip(scores[0], indices[0]), start=1):
            if index < 0 or index >= len(paths):
                continue

            image_path = str(paths[index])
            results.append(
                {
                    "rank": rank,
                    "brand_name": brands[index] if index < len(brands) else "unknown",
                    "category": categories[index] if index < len(categories) else "unknown",
                    "image_path": image_path,
                    "logo_similarity": float(max(0.0, min(1.0, score))),
                }
            )

        return results

    def _to_dataset_url(self, image_path: str) -> Optional[str]:
        try:
            root = Path(self.dataset_root).resolve()
            path = Path(image_path).resolve()
            rel = path.relative_to(root)
            rel_posix = "/".join(rel.parts)
            return f"/dataset-files/{quote(rel_posix)}"
        except Exception:
            return None

    @staticmethod
    def _format_legacy_results(results: List[Dict[str, object]]) -> List[Dict[str, object]]:
        formatted: List[Dict[str, object]] = []
        for item in results:
            similarity = float(item.get("logo_similarity", 0.0))
            image_path = str(item.get("image_path", ""))
            image_name = Path(image_path).name
            formatted.append(
                {
                    "rank": int(item.get("rank", len(formatted) + 1)),
                    "image_name": image_name,
                    "image_path": image_path,
                    "image_url": item.get("image_url"),
                    "category": item.get("category", "unknown"),
                    "brand_name": item.get("brand_name", "unknown"),
                    "similarity_score": similarity,
                    "similarity_percentage": round(similarity * 100.0, 2),
                    "distance": round(1.0 - similarity, 6),
                }
            )
        return formatted

    @staticmethod
    def _collision_risk_from_similarity(score: float) -> Dict[str, object]:
        if score > 0.85:
            risk_level = "HIGH"
            message = "High collision risk detected. Trademark is likely to already exist."
        elif score >= 0.65:
            risk_level = "MEDIUM"
            message = "Potential trademark similarity detected. Review recommended."
        else:
            risk_level = "LOW"
            message = "No strong trademark collision detected. Trademark appears safe."

        return {
            "risk_level": risk_level,
            "message": message,
            "similarity_score": float(score),
        }

    @staticmethod
    def _risk_from_score(score: float) -> str:
        if score > 0.85:
            return "High"
        if score >= 0.65:
            return "Medium"
        return "Low"

    def search_image_only(self, image_path: str, top_k: int = 5, detection_threshold: float = 0.65) -> Dict[str, object]:
        self._ensure_loaded()

        query_embedding = self.feature_extractor.extract_embedding(image_path)
        if query_embedding is None:
            raise RuntimeError("Failed to extract image embedding from input image.")

        image_results = self._search_image(query_embedding, top_k=top_k)
        for item in image_results:
            item["image_url"] = self._to_dataset_url(str(item.get("image_path", "")))
        best_score = float(image_results[0]["logo_similarity"]) if image_results else 0.0
        detected = best_score >= detection_threshold

        assert self.embeddings_payload is not None

        return {
            "uploaded_image": {
                "path": image_path,
                "url": f"/uploads/{Path(image_path).name}",
                "filename": Path(image_path).name,
            },
            "similar_trademarks": self._format_legacy_results(image_results),
            "collision_risk": self._collision_risk_from_similarity(best_score),
            "detected": detected,
            "top_score": best_score,
            "dataset": {
                "num_brands": int(self.embeddings_payload.get("num_brands", 0)),
                "num_categories": int(self.embeddings_payload.get("num_categories", 0)),
                "num_images": int(self.embeddings_payload.get("indexed_num_images", self.embeddings_payload.get("num_images", 0))),
                "full_dataset_num_images": int(self.embeddings_payload.get("full_dataset_num_images", self.embeddings_payload.get("num_images", 0))),
                "dataset_root": self.embeddings_payload.get("dataset_root"),
            },
        }

    def analyze_trademark(self, image_path: str, trademark_name: str, top_k: Optional[int] = None) -> Dict[str, object]:
        self._ensure_loaded()
        top_k = max(1, top_k or self.top_k_default)

        query_embedding = self.feature_extractor.extract_embedding(image_path)
        if query_embedding is None:
            raise RuntimeError("Failed to extract image embedding from input image.")

        image_results = self._search_image(query_embedding, top_k=top_k)
        for item in image_results:
            item["image_url"] = self._to_dataset_url(str(item.get("image_path", "")))
        name_results = self.name_engine.search_similar_names(trademark_name, top_k=top_k) if self.name_engine else []

        best_logo = float(image_results[0]["logo_similarity"]) if image_results else 0.0
        best_name = float(name_results[0]["similarity_score"]) if name_results else 0.0
        collision_score = best_logo
        risk_level = self._risk_from_score(collision_score)

        assert self.embeddings_payload is not None
        return {
            "input": {
                "name": trademark_name,
                "image_path": image_path,
            },
            "uploaded_image": {
                "path": image_path,
                "url": f"/uploads/{Path(image_path).name}",
                "filename": Path(image_path).name,
            },
            "similar_trademarks": self._format_legacy_results(image_results),
            "top_similar_logos": image_results,
            "top_similar_names": name_results,
            "scores": {
                "best_logo_similarity": round(best_logo, 6),
                "best_name_similarity": round(best_name, 6),
                "collision_score": round(collision_score, 6),
                "formula": "collision_score uses best_logo_similarity",
            },
            "collision_risk": {
                "risk_level": risk_level.upper(),
                "message": f"{risk_level} collision risk",
                "similarity_score": collision_score,
            },
            "risk": {
                "level": risk_level,
                "label": f"{risk_level} collision risk",
            },
            "dataset": {
                "num_brands": int(self.embeddings_payload.get("num_brands", 0)),
                "num_categories": int(self.embeddings_payload.get("num_categories", 0)),
                "num_images": int(self.embeddings_payload.get("indexed_num_images", self.embeddings_payload.get("num_images", 0))),
                "full_dataset_num_images": int(self.embeddings_payload.get("full_dataset_num_images", self.embeddings_payload.get("num_images", 0))),
                "dataset_root": self.embeddings_payload.get("dataset_root"),
            },
            "detected": bool(best_logo >= 0.65),
            "top_score": best_logo,
        }

    def get_statistics(self) -> Dict[str, object]:
        self._ensure_loaded()
        assert self.faiss_index.index is not None
        assert self.embeddings_payload is not None

        return {
            "total_trademarks": int(self.faiss_index.index.ntotal),
            "embedding_dimension": int(self.embeddings_payload.get("embedding_dim", 0)),
            "index_type": "IndexFlatIP (cosine)",
            "model": self.feature_extractor.backend,
            "num_brands": int(self.embeddings_payload.get("num_brands", 0)),
            "num_categories": int(self.embeddings_payload.get("num_categories", 0)),
            "indexed_num_images": int(self.embeddings_payload.get("indexed_num_images", self.embeddings_payload.get("num_images", 0))),
            "full_dataset_num_images": int(self.embeddings_payload.get("full_dataset_num_images", self.embeddings_payload.get("num_images", 0))),
            "dataset_root": self.embeddings_payload.get("dataset_root"),
            "generation_time_seconds": float(self.embeddings_payload.get("generation_time_seconds", 0)),
            "model_version": "3.0",
        }

    def run_self_match_test(self, top_k: int = 5, sample_size: int = 10) -> Dict[str, object]:
        self._ensure_loaded()
        all_paths = list(self.faiss_index.metadata.get("image_paths", []))
        brands = list(self.faiss_index.metadata.get("brands", []))
        if not all_paths:
            return {
                "success": False,
                "error": "No dataset records found",
                "tested_count": 0,
            }

        sampled_indices = random.sample(range(len(all_paths)), min(sample_size, len(all_paths)))
        test_results: List[Dict[str, object]] = []
        matches_success = 0

        for index in sampled_indices:
            query_path = str(all_paths[index])
            query_embedding = self.feature_extractor.extract_embedding(query_path)
            if query_embedding is None:
                continue

            results = self._search_image(query_embedding, top_k=top_k)
            top_match_path = results[0]["image_path"] if results else None
            matched_itself = top_match_path == query_path
            similarity = float(results[0]["logo_similarity"]) if results else 0.0
            passed = matched_itself and similarity > 0.90
            test_results.append(
                {
                    "image": Path(query_path).name,
                    "brand": brands[index] if index < len(brands) else "unknown",
                    "matched_itself": matched_itself,
                    "top_similarity": round(similarity, 4),
                    "passed": passed,
                }
            )
            if passed:
                matches_success += 1

        success_rate = matches_success / len(test_results) if test_results else 0.0
        return {
            "success": success_rate >= 0.8,
            "tested_count": len(test_results),
            "passed_count": matches_success,
            "success_rate": round(success_rate, 4),
            "details": test_results,
            "min_required_similarity": 0.90,
        }
