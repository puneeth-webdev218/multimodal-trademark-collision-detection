#!/usr/bin/env python
"""Test imports."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

print("Testing imports...")

try:
    print("1. Importing dataset_loader...")
    from dataset.dataset_loader import scan_logo_dataset
    print("   ✓ scan_logo_dataset imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

try:
    print("2. Importing feature_extractor...")
    from models.feature_extractor import FeatureExtractor
    print("   ✓ FeatureExtractor imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

try:
    print("3. Importing FAISS...")
    from similarity.faiss_index import FAISSIndex
    print("   ✓ FAISSIndex imported")
except Exception as e:
    print(f"   ❌ Failed: {e}")
    sys.exit(1)

print("\n✅ All imports successful!")

print("\n4. Quick dataset scan (no sampling)...")
payload = scan_logo_dataset()
print(f"   Found: {payload['num_images']} images in {payload['num_brands']} brands")
