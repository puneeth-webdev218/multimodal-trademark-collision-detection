"""
Demo Script for AI Trademark Collision Detection System
Demonstrates the similarity search functionality
"""

import requests
import os
from pathlib import Path

from dataset.dataset_loader import get_default_dataset_root, scan_logo_dataset

API_URL = "http://localhost:8000"

def print_header(text):
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def demo_upload_and_search(image_path, description=""):
    """Upload an image and find similar trademarks"""
    print(f"\n📤 Uploading: {os.path.basename(image_path)}")
    if description:
        print(f"   Description: {description}")
    
    # Upload the image
    with open(image_path, 'rb') as f:
        files = {'file': (os.path.basename(image_path), f, 'image/png')}
        data = {'top_k': 5, 'name': Path(image_path).parent.name}
        
        response = requests.post(f"{API_URL}/api/v1/analyze-trademark", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        
        # Display results
        print("\n✅ Analysis Complete!")
        print("-" * 40)
        
        analysis = result.get('results', {})
        risk = analysis.get('risk', {})
        risk_level = risk.get('level', 'UNKNOWN').upper()
        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk_level, "⚪")
        
        print(f"\n{risk_emoji} COLLISION RISK: {risk_level}")
        scores = analysis.get('scores', {})
        if scores.get('collision_score', 0) > 0:
            print(f"   Collision Score: {scores['collision_score']:.1%}")
        
        # Similar trademarks
        similar = analysis.get('top_similar_logos', [])
        print(f"\n🔍 Found {len(similar)} Similar Trademarks:")
        print("-" * 40)
        
        for i, tm in enumerate(similar, 1):
            score = tm.get('logo_similarity', 0) * 100
            name = tm.get('brand_name', 'Unknown')
            
            # Risk indicator
            if score >= 85:
                bar = "█████ HIGH"
            elif score >= 70:
                bar = "███░░ MED"
            else:
                bar = "█░░░░ LOW"
            
            print(f"  #{i} {name:<30} {score:>5.1f}% [{bar}]")
        
        return result
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)
        return None

def main():
    print_header("🛡️ AI TRADEMARK COLLISION DETECTION - DEMO")
    
    # Check API health
    print("\n📡 Checking API Status...")
    try:
        health = requests.get(f"{API_URL}/api/v1/health")
        if health.status_code == 200:
            print("   ✅ API is healthy!")
        else:
            print("   ⚠️ API health check failed")
            return
    except Exception as e:
        print(f"   ❌ Cannot connect to API: {e}")
        print("   Make sure the backend is running: cd backend && python main.py")
        return
    
    # Get stats
    print("\n📊 System Statistics:")
    stats = requests.get(f"{API_URL}/api/v1/stats").json()
    print(f"   • Total Trademarks in Database: {stats.get('total_trademarks', 0)}")
    print(f"   • Embedding Dimension: {stats.get('embedding_dimension', 0)}")
    print(f"   • Similarity Metric: {stats.get('index_type', 'cosine')}")
    print(f"   • Model: {stats.get('model', 'resnet50')}")
    
    dataset_root = get_default_dataset_root(Path(__file__).resolve().parent)
    scan = scan_logo_dataset(str(dataset_root))
    records = scan.get("records", [])

    if not records:
        print(f"No valid images found in: {dataset_root}")
        return

    for idx, record in enumerate(records[:4], start=1):
        print_header(f"DEMO {idx}: Testing {record.brand}")
        demo_upload_and_search(
            record.image_path,
            f"Auto-picked logo from dataset for brand '{record.brand}'"
        )
    
    print_header("DEMO COMPLETE")
    print("""
🎉 Demo completed successfully!

Next Steps:
1. Access the Swagger API docs: http://localhost:8000/docs
2. Run the React frontend: cd frontend && npm install && npm start
3. Open http://localhost:3000 in your browser

The system is ready to detect trademark collisions!
""")

if __name__ == "__main__":
    main()
