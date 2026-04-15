"""
Utility functions for the backend API
Helper functions for file handling, validation, and formatting
"""

import os
import shutil
from datetime import datetime
from PIL import Image
import uuid
from typing import List, Dict


def save_upload_file(upload_file, upload_dir='../uploads') -> str:
    """
    Save an uploaded file to the uploads directory
    
    Args:
        upload_file: FastAPI UploadFile object
        upload_dir: Directory to save files
        
    Returns:
        str: Path to saved file
    """
    # Create uploads directory if it doesn't exist
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_extension = get_file_extension(upload_file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Save file
    with open(file_path, 'wb') as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    return file_path


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        str: File extension with dot (e.g., '.jpg')
    """
    return os.path.splitext(filename)[1].lower()


def validate_image(image_path: str) -> bool:
    """
    Validate that a file is a valid image
    
    Args:
        image_path: Path to image file
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"Image validation failed: {str(e)}")
        return False


def get_image_url(image_path: str, base_url: str = "http://localhost:8000") -> str:
    """
    Convert local image path to URL
    
    Args:
        image_path: Local file path
        base_url: Base URL of the server
        
    Returns:
        str: Full URL to image
    """
    # Extract filename from path
    filename = os.path.basename(image_path)
    
    # Construct URL
    url = f"{base_url}/uploads/{filename}"
    
    return url


def format_search_results(results: List[Dict]) -> List[Dict]:
    """
    Format search results for API response
    
    Args:
        results: Raw search results
        
    Returns:
        List[Dict]: Formatted results
    """
    formatted_results = []
    
    for result in results:
        formatted_result = {
            'rank': result['rank'],
            'image_name': result['image_name'],
            'image_url': get_image_url(result['image_path']),
            'similarity_score': round(result['similarity_score'], 4),
            'similarity_percentage': round(result['similarity_score'] * 100, 2),
            'distance': round(result.get('distance', 0), 4)
        }
        formatted_results.append(formatted_result)
    
    return formatted_results


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: File size in bytes
        
    Returns:
        str: Formatted size (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def cleanup_old_uploads(upload_dir='../uploads', max_age_days=7):
    """
    Delete uploaded files older than specified days
    
    Args:
        upload_dir: Directory containing uploads
        max_age_days: Maximum age of files in days
    """
    if not os.path.exists(upload_dir):
        return
    
    current_time = datetime.now().timestamp()
    max_age_seconds = max_age_days * 24 * 60 * 60
    
    deleted_count = 0
    
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        
        if os.path.isfile(file_path):
            file_age = current_time - os.path.getmtime(file_path)
            
            if file_age > max_age_seconds:
                try:
                    os.remove(file_path)
                    deleted_count += 1
                    print(f"Deleted old file: {filename}")
                except Exception as e:
                    print(f"Error deleting {filename}: {str(e)}")
    
    print(f"Cleanup completed. Deleted {deleted_count} files.")


def get_supported_formats() -> List[str]:
    """
    Get list of supported image formats
    
    Returns:
        List[str]: Supported file extensions
    """
    return ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']


def is_supported_format(filename: str) -> bool:
    """
    Check if file format is supported
    
    Args:
        filename: Name of the file
        
    Returns:
        bool: True if supported, False otherwise
    """
    extension = get_file_extension(filename)
    return extension in get_supported_formats()


def create_thumbnail(image_path: str, size=(150, 150), output_dir='../uploads/thumbnails') -> str:
    """
    Create a thumbnail of an image
    
    Args:
        image_path: Path to original image
        size: Thumbnail size (width, height)
        output_dir: Directory to save thumbnails
        
    Returns:
        str: Path to thumbnail
    """
    os.makedirs(output_dir, exist_ok=True)
    
    filename = os.path.basename(image_path)
    thumbnail_path = os.path.join(output_dir, f"thumb_{filename}")
    
    try:
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path)
        
        return thumbnail_path
    except Exception as e:
        print(f"Error creating thumbnail: {str(e)}")
        return image_path


def get_image_info(image_path: str) -> Dict:
    """
    Get detailed information about an image
    
    Args:
        image_path: Path to image file
        
    Returns:
        Dict: Image information
    """
    try:
        with Image.open(image_path) as img:
            return {
                'format': img.format,
                'mode': img.mode,
                'size': img.size,
                'width': img.width,
                'height': img.height,
                'file_size': os.path.getsize(image_path),
                'file_size_formatted': format_file_size(os.path.getsize(image_path))
            }
    except Exception as e:
        return {
            'error': str(e)
        }
