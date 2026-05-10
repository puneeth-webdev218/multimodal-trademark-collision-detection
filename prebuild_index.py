#!/usr/bin/env python3
"""Offline pipeline: create subset, precompute embeddings, build FAISS index."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from dataset.dataset_loader import validate_logo_dataset
from dataset.subset_builder import build_subset
from models.generate_embeddings import load_or_generate_logo_embeddings
from similarity.faiss_index import build_index_from_embeddings
from similarity.search import SimilaritySearch


def main() -> None:
    parser = argparse.ArgumentParser(description="Build subset and precomputed FAISS artifacts")
    parser.add_argument("--max-images", type=int, default=100, help="Subset cap")
    parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
    parser.add_argument("--seed", type=int, default=42, help="Sampling seed")
    parser.add_argument("--build-subset-from-train", action="store_true", help="Rebuild subset from dataset/train before precomputing")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")

    base = Path(__file__).resolve().parent
    subset_root = base / "dataset" / "subset"
    emb_path = base / "models" / "logo_embeddings.pkl"
    idx_path = base / "similarity" / "faiss_index.index"
    meta_path = base / "similarity" / "index_metadata.pkl"

    if args.build_subset_from_train:
        train_root = base / "dataset" / "train"
        logging.info("Step 1/4 - Creating subset dataset from train")
        subset_summary = build_subset(
            source_root=train_root,
            subset_root=subset_root,
            max_images=max(1, args.max_images),
            seed=args.seed,
            clean=True,
        )
        logging.info("Subset summary: %s", subset_summary)
    else:
        logging.info("Step 1/4 - Validating existing subset dataset")
        subset_summary = validate_logo_dataset(str(subset_root))
        logging.info("Subset summary: %s", {"subset_images": subset_summary.get("num_images"), "num_categories": subset_summary.get("num_categories")})

    logging.info("Step 2/4 - Generating embeddings from subset")
    payload = load_or_generate_logo_embeddings(
        dataset_root=str(subset_root),
        embeddings_path=str(emb_path),
        model_name="clip",
        force_recompute=True,
        batch_size=max(1, args.batch_size),
    )
    logging.info("Embeddings ready: indexed=%s full=%s dim=%s", payload.get("indexed_num_images"), payload.get("full_dataset_num_images"), payload.get("embedding_dim"))

    logging.info("Step 3/4 - Building FAISS index")
    faiss_index = build_index_from_embeddings(str(emb_path), str(idx_path), str(meta_path))
    logging.info(
        "FAISS index built: index_size=%s expected=%s",
        faiss_index.index.ntotal if faiss_index.index is not None else 0,
        len(payload.get("image_paths", [])),
    )

    logging.info("Step 4/4 - Running self-match validation")
    search = SimilaritySearch(
        dataset_root=str(subset_root),
        embeddings_path=str(emb_path),
        index_path=str(idx_path),
        metadata_path=str(meta_path),
        model_name="clip",
    )
    validation = search.run_self_match_test(sample_size=min(10, max(1, int(payload.get("indexed_num_images", 1)))), top_k=5)
    logging.info("Validation summary: %s", validation)
    for item in validation.get("details", []):
        logging.info(
            "Self-match %s | brand=%s | passed=%s | similarity=%.4f",
            item.get("image"),
            item.get("brand"),
            item.get("passed"),
            float(item.get("top_similarity", 0.0)),
        )

    logging.info("Artifacts ready: embeddings=%s index=%s metadata=%s", emb_path.exists(), idx_path.exists(), meta_path.exists())


if __name__ == "__main__":
    main()
