#!/usr/bin/env python
"""Test just dataset_loader import."""
import sys
import time
from pathlib import Path

print(f"[{time.time()}] Adding to path...")
sys.path.insert(0, str(Path(__file__).parent))

print(f"[{time.time()}] About to import dataset_loader...")

# Try the import with timeout mechanism
try:
    from dataset.dataset_loader import scan_logo_dataset
    print(f"[{time.time()}] ✓ scan_logo_dataset imported successfully")
except Exception as e:
    print(f"[{time.time()}] ❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"[{time.time()}] Done!")
