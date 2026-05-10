#!/usr/bin/env python
"""Quick test of dataset scanning."""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent))

from dataset.dataset_loader import scan_logo_dataset

print("🔍 Testing dataset scan...")
start = time.time()
payload = scan_logo_dataset("dataset/train")
elapsed = time.time() - start

print(f"✓ Found {payload['num_images']} images in {payload['num_brands']} brands")
print(f"  Scan completed in {elapsed:.2f}s")

if payload['num_images'] > 0:
    print(f"  Sample paths: {payload['image_paths'][:3]}")
