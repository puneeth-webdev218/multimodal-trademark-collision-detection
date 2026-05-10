#!/usr/bin/env python3
"""Validation: query a subset image and verify top-1 self-match similarity."""

from __future__ import annotations

import random
from pathlib import Path

from similarity.search import SimilaritySearch


def main() -> None:
    project_root = Path(__file__).resolve().parent
    search = SimilaritySearch(
        dataset_root=str(project_root / "dataset" / "subset"),
        embeddings_path=str(project_root / "models" / "logo_embeddings.pkl"),
        index_path=str(project_root / "similarity" / "faiss_index.index"),
        metadata_path=str(project_root / "similarity" / "index_metadata.pkl"),
        model_name="auto",
    )

    stats = search.get_statistics()
    print(f"Loaded index with {stats['total_trademarks']} vectors")

    image_paths = list(search.faiss_index.metadata.get("image_paths", []))
    if not image_paths:
        raise RuntimeError("No image paths found in index metadata")

    query_path = random.choice(image_paths)
    print(f"Query image: {query_path}")

    result = search.search_image_only(image_path=query_path, top_k=5, detection_threshold=0.0)
    top_matches = result.get("similar_trademarks", [])

    if not top_matches:
        raise RuntimeError("No matches returned")

    print("Top 5 matches:")
    for item in top_matches[:5]:
        print(
            f"  #{item['rank']} | brand={item.get('brand_name')} | "
            f"score={item['similarity_score']:.4f} | path={item.get('image_path')}"
        )

    top1 = top_matches[0]
    same_image = Path(top1.get("image_path", "")).resolve() == Path(query_path).resolve()
    similarity = float(top1.get("similarity_score", 0.0))
    print(f"Top-1 same image: {same_image}")
    print(f"Top-1 similarity: {similarity:.4f}")

    if not same_image:
        raise AssertionError("Validation failed: top-1 match is not the same image")
    if similarity <= 0.90:
        raise AssertionError(f"Validation failed: expected similarity > 0.90, got {similarity:.4f}")

    print("Validation passed")


if __name__ == "__main__":
    main()
