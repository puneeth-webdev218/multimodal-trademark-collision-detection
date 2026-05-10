"""
Generate sample trademark images for testing the system
"""
import os
from PIL import Image, ImageDraw, ImageFont
import random

OUTPUT_DIR = os.path.join("dataset", "logos", "sample_generated")

# Create dataset directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Sample brand names and colors for generating test logos
brands = [
    ("TechCorp", "#3498db", "#ffffff"),
    ("InnovateTech", "#e74c3c", "#ffffff"),
    ("BlueSky", "#2980b9", "#ecf0f1"),
    ("GreenLeaf", "#27ae60", "#ffffff"),
    ("SunRise", "#f39c12", "#ffffff"),
    ("PurpleWave", "#9b59b6", "#ffffff"),
    ("RedFox", "#c0392b", "#ecf0f1"),
    ("OceanBlue", "#1abc9c", "#ffffff"),
    ("FireBird", "#e67e22", "#ffffff"),
    ("StarLight", "#34495e", "#f1c40f"),
    ("MountainView", "#16a085", "#ffffff"),
    ("CloudNine", "#3498db", "#ffffff"),
    ("DiamondCo", "#95a5a6", "#2c3e50"),
    ("GoldRush", "#f1c40f", "#2c3e50"),
    ("SilverLine", "#bdc3c7", "#2c3e50"),
]

def create_logo(name, bg_color, text_color, filename):
    """Create a simple logo image"""
    # Create image
    size = (300, 300)
    img = Image.new('RGB', size, bg_color)
    draw = ImageDraw.Draw(img)
    
    # Draw shapes based on name hash
    random.seed(hash(name) % 1000)
    
    # Draw background shape
    shape_type = random.choice(['circle', 'rectangle', 'triangle'])
    
    if shape_type == 'circle':
        margin = 40
        draw.ellipse([margin, margin, size[0]-margin, size[1]-margin], 
                     fill=bg_color, outline=text_color, width=8)
    elif shape_type == 'rectangle':
        margin = 50
        draw.rectangle([margin, margin, size[0]-margin, size[1]-margin], 
                       fill=bg_color, outline=text_color, width=6)
    else:  # triangle
        points = [(150, 40), (40, 260), (260, 260)]
        draw.polygon(points, fill=bg_color, outline=text_color)
    
    # Draw inner shape
    cx, cy = 150, 130
    r = 40
    inner_color = text_color
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], fill=inner_color)
    
    # Add text (brand initials)
    initials = ''.join([c for c in name if c.isupper()])[:2]
    if not initials:
        initials = name[:2].upper()
    
    # Draw text
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except:
        font = ImageFont.load_default()
    
    # Center text at bottom
    bbox = draw.textbbox((0, 0), initials, font=font)
    text_width = bbox[2] - bbox[0]
    text_x = (size[0] - text_width) // 2
    draw.text((text_x, 200), initials, fill=text_color, font=font)
    
    # Save
    img.save(filename)
    print(f"Created: {filename}")

# Generate logos
print("Generating sample trademark images...")
for i, (name, bg, fg) in enumerate(brands):
    filename = os.path.join(OUTPUT_DIR, f"logo_{i+1:02d}_{name.lower()}.png")
    create_logo(name, bg, fg, filename)

# Create some similar variations
print("\nCreating variations for similarity testing...")
variations = [
    ("TechCorp2", "#3498db", "#ffffff"),  # Similar to TechCorp
    ("TechCorpLite", "#5dade2", "#ffffff"),  # Similar to TechCorp
    ("BlueSkyPro", "#2980b9", "#ecf0f1"),  # Similar to BlueSky
    ("GreenLeafPlus", "#2ecc71", "#ffffff"),  # Similar to GreenLeaf
]

for i, (name, bg, fg) in enumerate(variations):
    filename = os.path.join(OUTPUT_DIR, f"logo_{len(brands)+i+1:02d}_{name.lower()}.png")
    create_logo(name, bg, fg, filename)

print(f"\nGenerated {len(brands) + len(variations)} sample trademark images!")
print(f"Images saved to: {OUTPUT_DIR}")
