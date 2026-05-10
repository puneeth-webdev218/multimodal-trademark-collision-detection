"""
API routes for trademark analysis.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.utils import get_image_url, save_upload_file, validate_image  # noqa: E402
from similarity.search import SimilaritySearch  # noqa: E402

LOGGER = logging.getLogger(__name__)
router = APIRouter()

_similarity_search: Optional[SimilaritySearch] = None
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif"}


def get_search_engine() -> SimilaritySearch:
    global _similarity_search
    if _similarity_search is None:
        LOGGER.info("Initializing similarity engine")
        _similarity_search = SimilaritySearch(
            dataset_root=str(PROJECT_ROOT / "dataset" / "subset"),
            embeddings_path=str(PROJECT_ROOT / "models" / "logo_embeddings.pkl"),
            index_path=str(PROJECT_ROOT / "similarity" / "faiss_index.index"),
            metadata_path=str(PROJECT_ROOT / "similarity" / "index_metadata.pkl"),
            name_embeddings_path=str(PROJECT_ROOT / "models" / "name_embeddings.pkl"),
            model_name="clip",
        )
    return _similarity_search


async def _handle_upload(file: UploadFile, top_k: int, trademark_name: Optional[str] = None) -> JSONResponse:
    start_time = time.time()
    upload_path = ""

    try:
        LOGGER.info("Request received for /analyze-trademark")
        if not file or not file.filename:
            raise HTTPException(status_code=400, detail="File is required")

        file_suffix = Path(file.filename).suffix.lower()
        if file.content_type and not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        if file_suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Unsupported image format. Allowed: jpg, jpeg, png, webp, bmp, gif")

        top_k = max(1, min(int(top_k), 20))
        trademark_name = (trademark_name or Path(file.filename).stem or "uploaded_logo").strip()

        LOGGER.info(
            "Received trademark request filename=%s content_type=%s top_k=%s name=%s",
            file.filename,
            file.content_type,
            top_k,
            trademark_name,
        )

        upload_path = save_upload_file(file)
        LOGGER.info("Upload saved to %s", upload_path)
        if not validate_image(upload_path):
            try:
                os.remove(upload_path)
            except Exception:
                pass
            raise HTTPException(status_code=400, detail="Invalid or corrupted image file")

        search_engine = get_search_engine()
        analysis = await asyncio.wait_for(
            asyncio.to_thread(
                search_engine.analyze_trademark,
                image_path=upload_path,
                trademark_name=trademark_name,
                top_k=top_k,
            ),
            timeout=90,
        )

        LOGGER.info(
            "Query processed: best_logo_similarity=%.4f collision_risk=%s duration=%.2fs",
            float(analysis.get("scores", {}).get("best_logo_similarity", 0.0)),
            analysis.get("collision_risk", {}).get("risk_level"),
            time.time() - start_time,
        )

        response = {
            "status": "success",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "processing_time_seconds": round(time.time() - start_time, 2),
            "query": {
                "name": trademark_name,
                "uploaded_image_url": get_image_url(upload_path),
                "uploaded_image_path": upload_path,
                "top_k": top_k,
            },
            "uploaded_image": analysis.get("uploaded_image", {"path": upload_path, "filename": Path(upload_path).name}),
            "similar_trademarks": analysis.get("similar_trademarks", []),
            "top_similar_logos": analysis.get("top_similar_logos", []),
            "top_similar_names": analysis.get("top_similar_names", []),
            "scores": analysis.get("scores", {}),
            "collision_risk": analysis.get("collision_risk", {}),
            "risk": analysis.get("risk", {}),
            "detected": analysis.get("detected", False),
            "top_score": analysis.get("top_score", 0.0),
            "dataset": analysis.get("dataset", {}),
        }

        return JSONResponse(content=response)
    except HTTPException as exc:
        LOGGER.warning("Request failed: %s", exc.detail)
        raise
    except TimeoutError:
        LOGGER.warning("Trademark analysis timed out")
        return JSONResponse(
            status_code=504,
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Analysis timeout",
                "detail": "Request took too long. Confirm that precomputed subset embeddings and FAISS index are built.",
            },
        )
    except Exception as exc:
        LOGGER.exception("Trademark analysis failed")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Failed to process image",
                "detail": str(exc),
            },
        )


@router.post("/analyze-trademark")
async def analyze_trademark(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    top_k: int = Form(5),
):
    return await _handle_upload(file=file, top_k=top_k, trademark_name=name)


@router.post("/upload")
async def upload_compat(
    file: UploadFile = File(...),
    top_k: int = Form(5),
):
    return await _handle_upload(file=file, top_k=top_k, trademark_name=Path(file.filename or "uploaded_logo").stem)


@router.get("/stats")
async def get_statistics():
    try:
        search_engine = get_search_engine()
        stats = await asyncio.wait_for(asyncio.to_thread(search_engine.get_statistics), timeout=30)
        return JSONResponse(content={"status": "operational", "timestamp": datetime.utcnow().isoformat() + "Z", **stats})
    except TimeoutError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "warming_up",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Index is still loading/building",
            },
        )
    except Exception as exc:
        LOGGER.exception("Failed to get statistics")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )


@router.get("/health")
async def health_check():
    try:
        initialized = _similarity_search is not None and _similarity_search._initialized
        backend_name = None
        if initialized and _similarity_search is not None:
            backend_name = _similarity_search.feature_extractor.backend
        return JSONResponse(
            content={
                "status": "healthy",
                "message": "All systems operational",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "initialized": initialized,
                "backend": backend_name,
            }
        )
    except Exception as exc:
        LOGGER.exception("Health check failed")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )


@router.post("/validate")
async def validate_system():
    try:
        search_engine = get_search_engine()
        validation = await asyncio.wait_for(
            asyncio.to_thread(search_engine.run_self_match_test, sample_size=10, top_k=5),
            timeout=120,
        )
        return JSONResponse(
            content={
                "status": "success" if validation.get("success") else "warning",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "validation": validation,
            }
        )
    except TimeoutError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "warming_up",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "message": "Validation timed out while index is warming up",
            },
        )
    except Exception as exc:
        LOGGER.exception("Validation failed")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(exc),
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
