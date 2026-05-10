#!/usr/bin/env python
"""
Ultra-fast embedding build for testing.
Samples 50 images per brand for quick verification that the pipeline works.
Real production build can run separately at larger scale.
"""
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from models.feature_extractor import FeatureExtractor
from similarity.faiss_index import FAISSIndex
from dataset.dataset_loader import scan_logo_dataset

def log(msg):
    """Print timestamped log message."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def build_sampled_embeddings():
    """Build embeddings for sampled dataset (fast validation run)."""
    dataset_root = Path("dataset/train")
    
    if not dataset_root.exists():
        log(f"❌ Dataset not found at {dataset_root}")
        return False
    
    log(f"📦 Starting sampled embedding generation (50 images per brand)")
    
    # Scan with sampling
    log("🔍 Scanning dataset (sampling 50 per brand)...")
    start = time.time()
    payload = scan_logo_dataset(str(dataset_root), sample_per_brand=50)
    elapsed = time.time() - start
    log(f"✓ Sampled: {payload['num_images']} images, {payload['num_brands']} brands in {elapsed:.1f}s")
    
    if payload['num_images'] == 0:
        log("❌ No images found!")
        return False
    
    # Generate embeddings
    log(f"⚙️  Extracting embeddings using ResNet50...")
    start = time.time()
    
    try:
        extractor = FeatureExtractor(model_type="resnet50")
        embeddings, kept_paths = extractor.extract_batch_embeddings_with_paths(
            payload['image_paths'],
            batch_size=64
        )
        elapsed = time.time() - start
        
        log(f"✓ Extracted {len(embeddings)} embeddings in {elapsed:.1f}s ({len(embeddings)/elapsed:.1f} img/s)")
        
        # Prepare final payload
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
    
    log("✅ Sampled embedding generation complete! Pipeline ready for testing.")
    log(f"   Now running on {payload['num_images']} images ({payload['num_brands']} brands)")
    return True

if __name__ == "__main__":
    success = build_sampled_embeddings()
    sys.exit(0 if success else 1)
