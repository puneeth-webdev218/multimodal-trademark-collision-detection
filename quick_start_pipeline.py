#!/usr/bin/env python3
"""
Quick Start: Build minimal 100-image subset for fast verification.
Run this first to confirm the entire pipeline works before scaling to 10k.
"""

from __future__ import annotations

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
LOGGER = logging.getLogger(__name__)


def quick_start() -> None:
    LOGGER.info("=" * 70)
    LOGGER.info("QUICK START: 100-Image Subset + Precompute Pipeline")
    LOGGER.info("=" * 70)

    base = Path(__file__).resolve().parent
    subset_root = base / "dataset" / "subset"

    if not subset_root.exists():
        LOGGER.error("Subset dataset not found at %s", subset_root)
        return

    LOGGER.info("\nStep 1: Validating existing 100-image subset...")
    from dataset.dataset_loader import validate_logo_dataset

    summary = validate_logo_dataset(str(subset_root))
    LOGGER.info("✓ Subset validated: %s images", summary.get("num_images"))

    LOGGER.info("\nStep 2: Generating embeddings...")
    from models.generate_embeddings import load_or_generate_logo_embeddings

    payload = load_or_generate_logo_embeddings(
        dataset_root=str(subset_root),
        embeddings_path=str(base / "models" / "logo_embeddings.pkl"),
        model_name="clip",
        force_recompute=True,
        batch_size=16,
    )
    LOGGER.info("✓ Embeddings ready: %s images indexed", payload.get("indexed_num_images"))

    LOGGER.info("\nStep 3: Building FAISS index...")
    from similarity.faiss_index import build_index_from_embeddings

    build_index_from_embeddings(
        str(base / "models" / "logo_embeddings.pkl"),
        str(base / "similarity" / "faiss_index.index"),
        str(base / "similarity" / "index_metadata.pkl"),
    )
    LOGGER.info("✓ FAISS index built")

    LOGGER.info("\nStep 4: Validating with self-match test...")
    from similarity.search import SimilaritySearch

    search = SimilaritySearch(dataset_root=str(subset_root))
    result = search.run_self_match_test(sample_size=5, top_k=5)
    LOGGER.info("✓ Validation result: %s (success_rate=%.1f%%)", result.get("success"), result.get("success_rate", 0) * 100)
    for item in result.get("details", []):
        LOGGER.info(
            "  %s | brand=%s | matched_itself=%s | similarity=%.4f",
            item.get("image"),
            item.get("brand"),
            item.get("matched_itself"),
            float(item.get("top_similarity", 0.0)),
        )

    LOGGER.info("\n" + "=" * 70)
    LOGGER.info("✅ QUICK START COMPLETE!")
    LOGGER.info("=" * 70)
    LOGGER.info("\nNext steps:")
    LOGGER.info("1. Start backend:  python -m backend.main")
    LOGGER.info("2. Start frontend: cd frontend && npm start")
    LOGGER.info("3. Upload a test image from dataset/subset to verify end-to-end flow")
    LOGGER.info("\nTo build full 10k subset:")
    LOGGER.info("  python prebuild_index.py --build-subset-from-train --max-images 10000")


if __name__ == "__main__":
    quick_start()
