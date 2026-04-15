"""
API Routes for Trademark Collision Detection
Handles upload, search, and analysis endpoints
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import shutil
from datetime import datetime
import sys
import json

# Add parent directories to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../similarity'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../models'))

from utils import (
    save_upload_file,
    get_file_extension,
    validate_image,
    format_search_results,
    get_image_url
)

# Import similarity search (will be initialized on first request)
similarity_search = None


router = APIRouter()


def get_search_engine():
    """
    Lazy load the similarity search engine
    """
    global similarity_search
    
    if similarity_search is None:
        try:
            from search import SimilaritySearch
            
            # Initialize search engine
            similarity_search = SimilaritySearch(
                index_path='../similarity/faiss_index.bin',
                metadata_path='../similarity/index_metadata.pkl',
                model_name='resnet50'
            )
            print("Similarity search engine initialized successfully")
        except Exception as e:
            print(f"Error initializing search engine: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize search engine. Please ensure embeddings and index are built."
            )
    
    return similarity_search


@router.post("/upload")
async def upload_trademark(
    file: UploadFile = File(...),
    top_k: int = Form(5)
):
    """
    Upload a trademark image and find similar trademarks
    
    Args:
        file: Uploaded image file
        top_k: Number of similar results to return
        
    Returns:
        JSON with uploaded image info and similar trademarks
    """
    # Validate file
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image (JPEG, PNG, etc.)"
        )
    
    try:
        # Save uploaded file
        upload_path = save_upload_file(file)
        
        # Validate image can be opened
        if not validate_image(upload_path):
            os.remove(upload_path)
            raise HTTPException(
                status_code=400,
                detail="Invalid or corrupted image file"
            )
        
        # Get search engine
        search_engine = get_search_engine()
        
        # Search for similar trademarks
        results = search_engine.search_similar(upload_path, top_k=top_k)
        
        # Calculate overall risk
        if results:
            highest_similarity = max(r['similarity_score'] for r in results)
            overall_risk = search_engine.calculate_collision_risk(highest_similarity)
        else:
            overall_risk = {
                'risk_level': 'LOW',
                'message': 'No similar trademarks found',
                'color': 'green',
                'similarity_score': 0.0
            }
        
        # Format response
        response = {
            'status': 'success',
            'uploaded_image': {
                'filename': os.path.basename(upload_path),
                'url': get_image_url(upload_path),
                'path': upload_path
            },
            'similar_trademarks': format_search_results(results),
            'collision_risk': overall_risk,
            'total_results': len(results),
            'timestamp': datetime.now().isoformat()
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing image: {str(e)}"
        )


@router.post("/search")
async def search_trademark(
    image_path: str = Form(...)
):
    """
    Search for similar trademarks using an existing image path
    
    Args:
        image_path: Path to the trademark image
        
    Returns:
        JSON with similar trademarks
    """
    if not os.path.exists(image_path):
        raise HTTPException(
            status_code=404,
            detail="Image file not found"
        )
    
    try:
        # Get search engine
        search_engine = get_search_engine()
        
        # Search for similar trademarks
        results = search_engine.search_similar(image_path, top_k=5)
        
        # Format response
        response = {
            'status': 'success',
            'query_image': image_path,
            'similar_trademarks': format_search_results(results),
            'total_results': len(results)
        }
        
        return JSONResponse(content=response)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching: {str(e)}"
        )


@router.get("/stats")
async def get_statistics():
    """
    Get system statistics and information
    
    Returns:
        JSON with system stats
    """
    try:
        # Get search engine
        search_engine = get_search_engine()
        
        # Get statistics
        stats = search_engine.get_statistics()
        
        # Add additional info
        stats['status'] = 'operational'
        stats['api_version'] = '1.0.0'
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        return JSONResponse(
            content={
                'status': 'error',
                'message': str(e)
            },
            status_code=500
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint
    
    Returns:
        Health status
    """
    try:
        # Try to access search engine
        search_engine = get_search_engine()
        
        return {
            'status': 'healthy',
            'message': 'All systems operational',
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {
            'status': 'unhealthy',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }


@router.delete("/uploads/{filename}")
async def delete_upload(filename: str):
    """
    Delete an uploaded file
    
    Args:
        filename: Name of the file to delete
        
    Returns:
        Success message
    """
    file_path = os.path.join("../uploads", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    
    try:
        os.remove(file_path)
        return {
            'status': 'success',
            'message': f'File {filename} deleted successfully'
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file: {str(e)}"
        )


@router.get("/list-uploads")
async def list_uploads():
    """
    List all uploaded files
    
    Returns:
        List of uploaded files
    """
    upload_dir = "../uploads"
    
    if not os.path.exists(upload_dir):
        return {
            'status': 'success',
            'uploads': [],
            'count': 0
        }
    
    files = []
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        if os.path.isfile(file_path):
            files.append({
                'filename': filename,
                'url': get_image_url(file_path),
                'size': os.path.getsize(file_path),
                'modified': datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    return {
        'status': 'success',
        'uploads': files,
        'count': len(files)
    }
