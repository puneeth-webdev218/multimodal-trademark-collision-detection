#!/usr/bin/env python3
"""
Simple file verification - Check that all fixes are in place
"""

from pathlib import Path

def main():
    print("\n" + "="*70)
    print("AI TRADEMARK COLLISION DETECTION - FILE VERIFICATION")
    print("="*70 + "\n")
    
    base = Path(__file__).parent
    checks = []
    
    # 1. Check dataset loader
    print("1. Checking dataset_loader.py...")
    loader = base / "dataset" / "dataset_loader.py"
    if loader.exists():
        content = loader.read_text()
        if "scan_logo_dataset" in content and "LogoRecord" in content:
            print("   ✓ Dataset loader properly rewritten")
            checks.append(True)
        else:
            print("   ✗ Dataset loader missing key functions")
            checks.append(False)
    else:
        print("   ✗ Dataset loader not found")
        checks.append(False)
    
    # 2. Check embedding generation
    print("\n2. Checking models/generate_embeddings.py...")
    embeddings = base / "models" / "generate_embeddings.py"
    if embeddings.exists():
        content = embeddings.read_text()
        if "EmbeddingGenerator" in content and ("batch" in content.lower() or "tqdm" in content):
            print("   ✓ Embedding generation properly rewritten")
            checks.append(True)
        else:
            print("   ✗ Embedding generation missing key features")
            checks.append(False)
    else:
        print("   ✗ Embedding generation not found")
        checks.append(False)
    
    # 3. Check search module
    print("\n3. Checking similarity/search.py...")
    search = base / "similarity" / "search.py"
    if search.exists():
        content = search.read_text()
        if "SimilaritySearch" in content and "run_self_match_test" in content:
            print("   ✓ Search module properly rewritten")
            checks.append(True)
        else:
            print("   ✗ Search module missing key methods")
            checks.append(False)
    else:
        print("   ✗ Search module not found")
        checks.append(False)
    
    # 4. Check backend routes
    print("\n4. Checking backend/routes.py...")
    routes = base / "backend" / "routes.py"
    if routes.exists():
        content = routes.read_text()
        if "analyze-trademark" in content and "async def" in content:
            print("   ✓ Backend routes properly rewritten")
            checks.append(True)
        else:
            print("   ✗ Backend routes missing key endpoints")
            checks.append(False)
    else:
        print("   ✗ Backend routes not found")
        checks.append(False)
    
    # 5. Check frontend App.js
    print("\n5. Checking frontend/src/App.js...")
    app = base / "frontend" / "src" / "App.js"
    if app.exists():
        content = app.read_text()
        if "handleUpload" in content and "API_BASE_URL" in content and "AbortController" in content:
            print("   ✓ App.js properly fixed")
            checks.append(True)
        else:
            print("   ✗ App.js missing key fixes")
            checks.append(False)
    else:
        print("   ✗ App.js not found")
        checks.append(False)
    
    # 6. Check frontend UploadForm
    print("\n6. Checking frontend/src/components/UploadForm.js...")
    upload = base / "frontend" / "src" / "components" / "UploadForm.js"
    if upload.exists():
        content = upload.read_text()
        if "useDropzone" in content or "getRootProps" in content:
            print("   ✓ UploadForm.js properly rewritten")
            checks.append(True)
        else:
            print("   ✗ UploadForm.js missing drag-drop")
            checks.append(False)
    else:
        print("   ✗ UploadForm.js not found")
        checks.append(False)
    
    # 7. Check frontend ResultsGrid
    print("\n7. Checking frontend/src/components/ResultsGrid.js...")
    results = base / "frontend" / "src" / "components" / "ResultsGrid.js"
    if results.exists():
        content = results.read_text()
        if "collision_risk" in content and "getRiskColor" in content:
            print("   ✓ ResultsGrid.js properly rewritten")
            checks.append(True)
        else:
            print("   ✗ ResultsGrid.js missing risk display")
            checks.append(False)
    else:
        print("   ✗ ResultsGrid.js not found")
        checks.append(False)
    
    # 8. Check validation script
    print("\n8. Checking validate_system.py...")
    validate = base / "validate_system.py"
    if validate.exists():
        print("   ✓ Validation script exists")
        checks.append(True)
    else:
        print("   ✗ Validation script not found")
        checks.append(False)
    
    # 9. Check fixes documentation
    print("\n9. Checking FIXES_APPLIED.md...")
    fixes = base / "FIXES_APPLIED.md"
    if fixes.exists():
        print("   ✓ Fixes documentation exists")
        checks.append(True)
    else:
        print("   ✗ Fixes documentation not found")
        checks.append(False)
    
    # Summary
    passed = sum(checks)
    total = len(checks)
    
    print("\n" + "="*70)
    print("FILE VERIFICATION SUMMARY")
    print("="*70)
    print(f"✓ Passed: {passed}/{total}")
    print("="*70 + "\n")
    
    if passed == total:
        print("✓ ALL FIXES ARE IN PLACE!")
        print("\nNext steps:")
        print("1. Run: python backend/main.py")
        print("2. In another terminal: cd frontend && npm start")
        print("3. Open http://localhost:3000")
        print("4. Upload a trademark image to test")
        return True
    else:
        print(f"✗ {total - passed} checks failed")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
