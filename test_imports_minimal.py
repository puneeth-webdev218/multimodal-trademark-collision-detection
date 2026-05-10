#!/usr/bin/env python
"""Test each import from dataset_loader individually."""

print("1. Testing: import os")
import os
print("   ✓ os imported")

print("2. Testing: from dataclasses import dataclass")
from dataclasses import dataclass
print("   ✓ dataclass imported")

print("3. Testing: from pathlib import Path")
from pathlib import Path
print("   ✓ Path imported")

print("4. Testing: from typing import Dict, List, Optional, Sequence")
from typing import Dict, List, Optional, Sequence
print("   ✓ typing imports ok")

print("5. Testing: import numpy as np")
import numpy as np
print("   ✓ numpy imported")

print("6. Testing: import torch")
import torch
print("   ✓ torch imported")

print("7. Testing: from PIL import Image, UnidentifiedImageError")
from PIL import Image, UnidentifiedImageError
print("   ✓ PIL imports ok")

print("8. Testing: from torchvision import transforms")
from torchvision import transforms
print("   ✓ torchvision.transforms imported")

print("\n✅ All imports succeeded!")
