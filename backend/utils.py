"""
Utility functions for the backend API.
"""

from __future__ import annotations

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = PROJECT_ROOT / "uploads"


def save_upload_file(upload_file, upload_dir: Path | str = UPLOAD_DIR) -> str:
    upload_dir = Path(upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    filename = upload_file.filename or "upload"
    extension = get_file_extension(filename)
    unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{extension}"
    file_path = upload_dir / unique_filename

    with file_path.open("wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return str(file_path)


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def validate_image(image_path: str) -> bool:
    try:
        with Image.open(image_path) as image:
            image.verify()
        with Image.open(image_path) as image:
            image.convert("RGB")
        return True
    except Exception:
        return False


def get_image_url(image_path: str, base_url: str = "") -> str:
    filename = os.path.basename(image_path)
    prefix = base_url.rstrip("/") if base_url else ""
    return f"{prefix}/uploads/{filename}"


def format_search_results(results: List[Dict]) -> List[Dict]:
    formatted_results = []
    for result in results:
        similarity_score = float(result.get("similarity_score", 0.0))
        formatted_results.append(
            {
                "rank": result.get("rank"),
                "image_name": result.get("image_name"),
                "image_url": get_image_url(result.get("image_path", "")),
                "similarity_score": round(similarity_score, 4),
                "similarity_percentage": round(similarity_score * 100, 2),
                "distance": round(float(result.get("distance", 0.0)), 4),
            }
        )
    return formatted_results


def format_file_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def cleanup_old_uploads(upload_dir: Path | str = UPLOAD_DIR, max_age_days: int = 7) -> None:
    upload_dir = Path(upload_dir)
    if not upload_dir.exists():
        return

    current_time = datetime.now().timestamp()
    max_age_seconds = max_age_days * 24 * 60 * 60

    for file_path in upload_dir.iterdir():
        if file_path.is_file():
            file_age = current_time - file_path.stat().st_mtime
            if file_age > max_age_seconds:
                try:
                    file_path.unlink()
                except Exception:
                    pass


def get_supported_formats() -> List[str]:
    return [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp"]


def is_supported_format(filename: str) -> bool:
    return get_file_extension(filename) in get_supported_formats()


def create_thumbnail(image_path: str, size=(150, 150), output_dir: Path | str = UPLOAD_DIR / "thumbnails") -> str:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = os.path.basename(image_path)
    thumbnail_path = output_dir / f"thumb_{filename}"

    try:
        with Image.open(image_path) as image:
            image = image.convert("RGB")
            image.thumbnail(size, Image.Resampling.LANCZOS)
            image.save(thumbnail_path)
        return str(thumbnail_path)
    except Exception:
        return image_path


def get_image_info(image_path: str) -> Dict:
    try:
        with Image.open(image_path) as image:
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "file_size": os.path.getsize(image_path),
                "file_size_formatted": format_file_size(os.path.getsize(image_path)),
            }
    except Exception as exc:
        return {"error": str(exc)}
