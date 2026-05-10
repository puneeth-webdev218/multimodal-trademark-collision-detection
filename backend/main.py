"""
FastAPI backend for trademark collision detection.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routes import get_search_engine, router

PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPLOAD_DIR = PROJECT_ROOT / "uploads"
SUBSET_DIR = PROJECT_ROOT / "dataset" / "subset"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="AI Trademark Collision Detection API",
    description="Trademark collision detection and logo similarity search",
    version="3.0.0",
)

frontend_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
allowed_origins = [origin.strip() for origin in frontend_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
if SUBSET_DIR.exists():
    app.mount("/dataset-files", StaticFiles(directory=str(SUBSET_DIR)), name="dataset-files")
app.include_router(router, prefix="/api/v1")


@app.on_event("startup")
async def preload_similarity_engine() -> None:
    if os.getenv("PRELOAD_INDEX_ON_STARTUP", "1").lower() not in {"1", "true", "yes"}:
        LOGGER.info("Similarity engine will load lazily on first request")
        return

    try:
        engine = get_search_engine()
        _ = engine.get_statistics()
        LOGGER.info("Similarity engine preloaded successfully")
    except FileNotFoundError as exc:
        LOGGER.warning(
            "Precomputed artifacts missing (expected for first startup): %s. "
            "Run: python prebuild_index.py --max-images 10000",
            exc,
        )
    except Exception as exc:
        LOGGER.warning("Similarity engine preload failed (will retry on first request): %s", exc)


@app.get("/")
async def root():
    return {
        "message": "AI Trademark Collision Detection API",
        "version": "3.0.0",
        "endpoints": {
            "analyze_trademark": "/api/v1/analyze-trademark",
            "upload": "/api/v1/upload",
            "health": "/api/v1/health",
            "stats": "/api/v1/stats",
            "validate": "/api/v1/validate",
        },
        "documentation": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Service is running"}


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
