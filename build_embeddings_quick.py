#!/usr/bin/env python
"""
Fast embedding build for selected categories to get system working quickly.
Focuses on Accessories and Clothes first (35k+ images).
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from models.feature_extractor import FeatureExtractor
from models.generate_embeddings import generate_embeddings
from similarity.faiss_index import FAISSIndex
from dataset.dataset_loader import scan_logo_dataset

def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

def build_partial_embeddings(categories=None):
    """
    Build embeddings for selected categories only.
    Categories: list of folder names under dataset/train, e.g., ["Accessories", "Clothes"]
    If None, builds all.
    """
    dataset_root = Path("dataset/train")
    
    if not dataset_root.exists():
        log(f"❌ Dataset not found at {dataset_root}")
        return False
    
    log(f"📦 Starting embedding generation for dataset at {dataset_root}")
    
    # Scan dataset
    log("🔍 Scanning dataset...")
    start = time.time()
    payload = scan_logo_dataset(str(dataset_root))
    elapsed = time.time() - start
    log(f"✓ Dataset scanned in {elapsed:.1f}s: {payload['num_images']} images, {payload['num_brands']} brands")
    
    # Filter to selected categories if requested
    if categories:
        log(f"📁 Filtering to categories: {categories}")
        original_image_count = payload['num_images']
        
        filtered_paths = []
        filtered_brands = set()
        
        for path in payload['image_paths']:
            path_obj = Path(path)
            # Extract category from path (first folder under dataset/train)
            try:
                rel_parts = path_obj.relative_to(dataset_root).parts
                if rel_parts[0] in categories:
                    filtered_paths.append(path)
                    # Figure out brand from path
                    if len(rel_parts) >= 3:
                        filtered_brands.add(rel_parts[1])
            except:
                pass
        
        payload['image_paths'] = filtered_paths
        payload['num_images'] = len(filtered_paths)
        payload['num_brands'] = len(filtered_brands)
        log(f"✓ Filtered: {original_image_count} → {payload['num_images']} images, {payload['num_brands']} brands")
    
    if payload['num_images'] == 0:
        log("❌ No images found!")
        return False
    
    # Generate embeddings
    log(f"⚙️  Extracting embeddings using ResNet50 (batch_size=64)...")
    start = time.time()
    
    try:
        extractor = FeatureExtractor(model_type="resnet50")
        embeddings, kept_paths = extractor.extract_batch_embeddings_with_paths(
            payload['image_paths'],
            batch_size=64
        )
        elapsed = time.time() - start
        
        log(f"✓ Extracted {len(embeddings)} embeddings in {elapsed:.1f}s ({len(embeddings)/elapsed:.1f} img/s)")
        
        # Prepare payload
        payload['embeddings'] = embeddings
        payload['image_paths'] = kept_paths
        payload['num_images'] = len(embeddings)
        
    except Exception as e:
        log(f"❌ Embedding extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Build and save FAISS index
    log("🔨 Building FAISS IndexFlatIP...")
    start = time.time()
    
    try:
        faiss_index = FAISSIndex()
        faiss_index.load_or_build(payload)
        elapsed = time.time() - start
        log(f"✓ FAISS index built in {elapsed:.1f}s")
        
    except Exception as e:
        log(f"❌ FAISS index build failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Save embeddings payload
    log("💾 Saving embedding cache...")
    try:
        import pickle
        cache_path = Path("models/logo_embeddings.pkl")
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, 'wb') as f:
            pickle.dump(payload, f)
        file_size_mb = cache_path.stat().st_size / (1024 * 1024)
        log(f"✓ Cache saved to {cache_path} ({file_size_mb:.1f} MB)")
        
    except Exception as e:
        log(f"❌ Cache save failed: {e}")
        return False
    
    log("✅ Embedding generation complete!")
    return True

if __name__ == "__main__":
    # Build embeddings for Accessories + Clothes categories
    success = build_partial_embeddings(categories=["Accessories", "Clothes"])
    sys.exit(0 if success else 1)
