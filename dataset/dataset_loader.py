"""Dataset loading utilities for trademark/logo images.

This loader recursively scans the subset dataset and records:
- image path
- category folder
- brand folder

Corrupted or unsupported files are ignored.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Set

import numpy as np
from PIL import Image, UnidentifiedImageError

LOGGER = logging.getLogger(__name__)

VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}


@dataclass(frozen=True)
class LogoRecord:
    category: str
    brand: str
    image_path: str


def get_default_dataset_root(project_root: Optional[Path] = None) -> Path:
    base = project_root or Path(__file__).resolve().parents[1]
    candidates = [base / "dataset" / "subset", base / "dataset" / "train", base / "dataset" / "logos"]

    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate

    return candidates[0]


def _is_valid_image(path: Path) -> bool:
    if path.suffix.lower() not in VALID_IMAGE_EXTENSIONS:
        return False

    try:
        with Image.open(path) as img:
            img.verify()
        return True
    except (UnidentifiedImageError, OSError, ValueError):
        return False
    except Exception:
        return False


def _derive_category_and_brand(root: Path, image_path: Path) -> tuple[str, str]:
    relative_parts = image_path.relative_to(root).parts

    if not relative_parts:
        return "uncategorized", image_path.parent.name or image_path.stem or "unknown"

    category = relative_parts[0]
    brand = image_path.parent.name or image_path.stem or "unknown"
    return category, brand


def scan_logo_dataset(dataset_root: Optional[str] = None, sample_per_brand: Optional[int] = None) -> Dict[str, object]:
    root = Path(dataset_root) if dataset_root else get_default_dataset_root()
    root = root.resolve()

    records: List[LogoRecord] = []
    skipped_invalid = 0
    categories: Set[str] = set()
    brand_to_paths: Dict[str, List[str]] = {}
    brand_to_category: Dict[str, str] = {}

    LOGGER.info("Scanning dataset root: %s", root)

    if not root.exists():
        LOGGER.warning("Dataset root does not exist: %s", root)
        return {
            "dataset_root": str(root),
            "records": [],
            "categories": [],
            "brands": [],
            "brand_to_paths": {},
            "category_to_brands": {},
            "num_images": 0,
            "num_brands": 0,
            "num_categories": 0,
            "skipped_invalid": 0,
        }

    for dirpath, _, filenames in os.walk(root):
        directory = Path(dirpath)
        for filename in filenames:
            file_path = directory / filename
            if file_path.suffix.lower() not in VALID_IMAGE_EXTENSIONS:
                continue

            if not _is_valid_image(file_path):
                skipped_invalid += 1
                LOGGER.debug("Skipping corrupted image: %s", file_path)
                continue

            category, brand = _derive_category_and_brand(root, file_path)
            categories.add(category)
            brand_to_category[brand] = category
            # Avoid Path.resolve() on every file here; Windows can hit resource limits on large scans.
            brand_to_paths.setdefault(brand, []).append(str(file_path))

    if sample_per_brand and sample_per_brand > 0:
        import random

        sampled: Dict[str, List[str]] = {}
        for brand, paths in brand_to_paths.items():
            sampled[brand] = random.sample(paths, min(sample_per_brand, len(paths)))
        brand_to_paths = sampled

    for brand, paths in brand_to_paths.items():
        category = brand_to_category.get(brand, "uncategorized")
        for image_path in paths:
            records.append(LogoRecord(category=category, brand=brand, image_path=image_path))

    records.sort(key=lambda record: record.image_path)
    brands = sorted(brand_to_paths.keys())
    category_to_brands: Dict[str, List[str]] = {}
    for brand, category in brand_to_category.items():
        category_to_brands.setdefault(category, []).append(brand)

    for brand_list in category_to_brands.values():
        brand_list.sort()

    LOGGER.info(
        "Dataset scan complete: %s images, %s brands, %s categories, %s invalid skipped",
        len(records),
        len(brands),
        len(categories),
        skipped_invalid,
    )

    return {
        "dataset_root": str(root),
        "records": records,
        "categories": sorted(categories),
        "brands": brands,
        "brand_to_paths": brand_to_paths,
        "category_to_brands": category_to_brands,
        "num_images": len(records),
        "num_brands": len(brands),
        "num_categories": len(categories),
        "skipped_invalid": skipped_invalid,
    }


def validate_logo_dataset(dataset_root: Optional[str] = None) -> Dict[str, object]:
    summary = scan_logo_dataset(dataset_root=dataset_root)
    LOGGER.info("Validated dataset root: %s", summary["dataset_root"])
    LOGGER.info("Total images loaded: %s", summary["num_images"])
    LOGGER.info("Total categories: %s", summary["num_categories"])
    for record in summary["records"]:
        LOGGER.info("Image: %s", record.image_path)
    return summary


def load_image_rgb(image_path: str) -> Image.Image:
    with Image.open(image_path) as img:
        return img.convert("RGB")


def preprocess_image(image: Image.Image, image_size: int = 224) -> Image.Image:
    return image.convert("RGB").resize((image_size, image_size), Image.Resampling.LANCZOS)


def preprocess_image_path(image_path: str, image_size: int = 224) -> Image.Image:
    image = load_image_rgb(image_path)
    return preprocess_image(image=image, image_size=image_size)


def preprocess_images_to_batch(images: Sequence[Image.Image], image_size: int = 224) -> List[Image.Image]:
    return [preprocess_image(image, image_size=image_size) for image in images]


def l2_normalize(vectors: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, eps, None)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    summary = validate_logo_dataset()
    print(f"Dataset root: {summary['dataset_root']}")
    print(f"Images loaded: {summary['num_images']}")
    print(f"Brands loaded: {summary['num_brands']}")
    print(f"Categories loaded: {summary['num_categories']}")
    print(f"Skipped invalid images: {summary['skipped_invalid']}")
