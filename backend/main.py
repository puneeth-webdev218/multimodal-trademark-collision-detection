"""
FastAPI Backend for Trademark Collision Detection System
Main application entry point
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from routes import router
import uvicorn


# Create FastAPI app
app = FastAPI(
    title="AI Trademark Collision Detection API",
    description="Deep Learning-powered trademark similarity detection system",
    version="1.0.0"
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files (uploaded images)
if not os.path.exists("../uploads"):
    os.makedirs("../uploads")

app.mount("/uploads", StaticFiles(directory="../uploads"), name="uploads")

# Include routers
app.include_router(router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "message": "AI Trademark Collision Detection API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/v1/upload",
            "search": "/api/v1/search",
            "health": "/api/v1/health",
            "stats": "/api/v1/stats"
        },
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Service is running"
    }


if __name__ == "__main__":
    # Run the application
    print("="*60)
    print("Starting AI Trademark Collision Detection API")
    print("="*60)
    print("API Documentation: http://localhost:8000/docs")
    print("API Base URL: http://localhost:8000")
    print("="*60)
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
