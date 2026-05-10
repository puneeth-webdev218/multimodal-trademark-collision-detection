#!/usr/bin/env python
"""Simple test to see what's hanging."""
import sys
import time

print(f"[{time.time()}] Starting imports...")

try:
    print(f"[{time.time()}] Importing torch...")
    import torch
    print(f"[{time.time()}] ✓ torch imported")
except Exception as e:
    print(f"[{time.time()}] ❌ torch failed: {e}")

try:
    print(f"[{time.time()}] Importing torchvision...")
    from torchvision import transforms
    print(f"[{time.time()}] ✓ torchvision imported")
except Exception as e:
    print(f"[{time.time()}] ❌ torchvision failed: {e}")

try:
    print(f"[{time.time()}] Importing PIL...")
    from PIL import Image
    print(f"[{time.time()}] ✓ PIL imported")
except Exception as e:
    print(f"[{time.time()}]  ❌ PIL failed: {e}")

try:
    print(f"[{time.time()}] Importing pathlib...")
    from pathlib import Path
    print(f"[{time.time()}] ✓ pathlib imported")
except Exception as e:
    print(f"[{time.time()}] ❌ pathlib failed: {e}")

print(f"[{time.time()}] All basic imports successful!")
