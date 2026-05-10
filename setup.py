"""
Setup Script for AI Trademark Collision Detection System
Run this script to initialize the system with your trademark dataset
"""

import os
import sys
import argparse
from pathlib import Path

from dataset.dataset_loader import get_default_dataset_root


def check_dependencies():
    """Check if required packages are installed"""
    required = ['torch', 'torchvision', 'faiss', 'PIL', 'numpy', 'tqdm', 'transformers', 'sentence_transformers']
    missing = []
    
    for package in required:
        try:
            if package == 'PIL':
                import PIL
            elif package == 'faiss':
                import faiss
            else:
                __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("Missing packages:", ", ".join(missing))
        print("Please install requirements: pip install -r requirements.txt")
        return False
    
    return True


def create_directories():
    """Create necessary directories"""
    dirs = [
        'dataset/logos',
        'uploads',
        'models',
        'similarity'
    ]
    
    base_dir = Path(__file__).parent
    
    for dir_path in dirs:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")


def generate_embeddings(dataset_path: str):
    """Generate embeddings for all trademark images"""
    sys.path.insert(0, str(Path(__file__).parent / 'models'))
    
    from generate_embeddings import load_or_generate_logo_embeddings
    
    payload = load_or_generate_logo_embeddings(
        dataset_root=dataset_path,
        embeddings_path=str(Path(__file__).parent / 'models' / 'logo_embeddings.pkl'),
        model_name='clip'
    )

    return payload is not None


def build_faiss_index():
    """Build FAISS index from embeddings"""
    sys.path.insert(0, str(Path(__file__).parent / 'similarity'))
    
    from faiss_index import build_index_from_embeddings
    
    base_dir = Path(__file__).parent
    
    build_index_from_embeddings(
        embeddings_path=str(base_dir / 'models' / 'logo_embeddings.pkl'),
        output_index=str(base_dir / 'similarity' / 'faiss_index.index'),
        output_metadata=str(base_dir / 'similarity' / 'index_metadata.pkl')
    )


def main():
    parser = argparse.ArgumentParser(
        description='Setup AI Trademark Collision Detection System'
    )
    parser.add_argument(
        '--dataset-path',
        type=str,
        default='',
        help='Path to trademark images directory (default: auto-detect dataset/logos then dataset/train)'
    )
    parser.add_argument(
        '--skip-embeddings',
        action='store_true',
        help='Skip embedding generation (use existing logo_embeddings.pkl)'
    )
    parser.add_argument(
        '--skip-index',
        action='store_true',
        help='Skip FAISS index building'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AI Trademark Collision Detection - Setup")
    print("=" * 60)
    
    # Check dependencies
    print("\n[1/4] Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    print("All dependencies installed!")
    
    # Create directories
    print("\n[2/4] Creating directories...")
    create_directories()
    
    # Check for images
    base_dir = Path(__file__).parent
    dataset_dir = (base_dir / args.dataset_path) if args.dataset_path else get_default_dataset_root(base_dir)
    
    images = list(dataset_dir.glob('**/*.jpg')) + \
             list(dataset_dir.glob('**/*.jpeg')) + \
             list(dataset_dir.glob('**/*.png'))
    
    if len(images) == 0:
        print(f"\nWarning: No images found in {dataset_dir}")
        print("Please add trademark images and run setup again.")
        print("\nSupported formats: .jpg, .jpeg, .png")
        return
    
    print(f"\nFound {len(images)} trademark images")
    
    # Generate embeddings
    if not args.skip_embeddings:
        print("\n[3/4] Generating embeddings...")
        if not generate_embeddings(str(dataset_dir)):
            print("Failed to generate embeddings!")
            sys.exit(1)
    else:
        print("\n[3/4] Skipping embedding generation...")
    
    # Build FAISS index
    if not args.skip_index:
        print("\n[4/4] Building FAISS index...")
        build_faiss_index()
    else:
        print("\n[4/4] Skipping FAISS index building...")
    
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the backend: cd backend && python main.py")
    print("2. Start the frontend: cd frontend && npm start")
    print("3. Open http://localhost:3000 in your browser")
    print("=" * 60)


if __name__ == "__main__":
    main()
