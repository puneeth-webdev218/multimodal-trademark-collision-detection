"""
Demo Script for AI Trademark Collision Detection System
Demonstrates the similarity search functionality
"""

import requests
import os
import json
from PIL import Image

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
        data = {'top_k': 5}
        
        response = requests.post(f"{API_URL}/api/v1/upload", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        
        # Display results
        print("\n✅ Analysis Complete!")
        print("-" * 40)
        
        # Collision Risk
        risk = result.get('collision_risk', {})
        risk_level = risk.get('risk_level', 'UNKNOWN')
        risk_emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk_level, "⚪")
        
        print(f"\n{risk_emoji} COLLISION RISK: {risk_level}")
        print(f"   {risk.get('message', '')}")
        if risk.get('similarity_score', 0) > 0:
            print(f"   Highest Similarity: {risk['similarity_score']:.1%}")
        
        # Similar trademarks
        similar = result.get('similar_trademarks', [])
        print(f"\n🔍 Found {len(similar)} Similar Trademarks:")
        print("-" * 40)
        
        for i, tm in enumerate(similar, 1):
            score = tm.get('similarity_percentage', 0)
            name = tm.get('image_name', 'Unknown')
            
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
    
    # Demo 1: Test with a logo that has similar variations
    print_header("DEMO 1: Testing TechCorp Logo (has similar variations)")
    demo_upload_and_search(
        "dataset/trademarks/logo_01_techcorp.png",
        "Original TechCorp logo - should find TechCorp2 and TechCorpLite as similar"
    )
    
    # Demo 2: Test with BlueSky
    print_header("DEMO 2: Testing BlueSky Logo")
    demo_upload_and_search(
        "dataset/trademarks/logo_03_bluesky.png",
        "BlueSky logo - should find BlueskyPro as similar"
    )
    
    # Demo 3: Test with a unique logo
    print_header("DEMO 3: Testing FireBird Logo (unique style)")
    demo_upload_and_search(
        "dataset/trademarks/logo_09_firebird.png",
        "FireBird logo - should have lower similarity scores"
    )
    
    # Demo 4: Test similar variation
    print_header("DEMO 4: Testing TechCorpLite (variation)")
    demo_upload_and_search(
        "dataset/trademarks/logo_17_techcorplite.png",
        "TechCorpLite - should highly match with TechCorp original"
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
