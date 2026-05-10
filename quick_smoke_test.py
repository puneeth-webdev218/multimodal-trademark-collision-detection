#!/usr/bin/env python3
"""
Quick Smoke Test - Verify core fixes work without full dataset processing
"""

import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
LOGGER = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported"""
    LOGGER.info("\n1. Testing imports...")
    try:
        from dataset.dataset_loader import scan_logo_dataset, LogoRecord
        from models.generate_embeddings import load_or_generate_logo_embeddings, EmbeddingGenerator
        from similarity.search import SimilaritySearch
        from backend.routes import router, get_search_engine
        LOGGER.info("   ✓ All imports successful")
        return True
    except Exception as e:
        LOGGER.error(f"   ✗ Import failed: {e}")
        return False

def test_dataset_structure():
    """Test that dataset structure is correctly detected"""
    LOGGER.info("\n2. Testing dataset structure detection...")
    try:
        from dataset.dataset_loader import scan_logo_dataset
        
        result = scan_logo_dataset(verbose=False)
        
        LOGGER.info(f"   Dataset root: {result['dataset_root']}")
        LOGGER.info(f"   Categories found: {result['num_categories']}")
        LOGGER.info(f"   Brands found: {result['num_brands']}")
        LOGGER.info(f"   Images found: {result['num_images']}")
        
        assert result['num_images'] > 0, "No images found"
        assert result['num_brands'] > 0, "No brands found"
        
        LOGGER.info("   ✓ Dataset structure test passed")
        return True
    except Exception as e:
        LOGGER.error(f"   ✗ Dataset structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_moves():
    """Test that all files were moved correctly"""
    LOGGER.info("\n3. Testing file moves...")
    try:
        base = Path(__file__).parent
        
        files_to_check = [
            base / "dataset" / "dataset_loader.py",
            base / "models" / "generate_embeddings.py",
            base / "similarity" / "search.py",
            base / "backend" / "routes.py",
            base / "frontend" / "src" / "App.js",
            base / "frontend" / "src" / "components" / "UploadForm.js",
            base / "frontend" / "src" / "components" / "ResultsGrid.js",
        ]
        
        missing = []
        for f in files_to_check:
            if not f.exists():
                missing.append(str(f))
        
        if missing:
            LOGGER.error("   ✗ Missing files:")
            for f in missing:
                LOGGER.error(f"     - {f}")
            return False
        
        LOGGER.info(f"   ✓ All {len(files_to_check)} files exist")
        return True
    except Exception as e:
        LOGGER.error(f"   ✗ File check failed: {e}")
        return False

def test_backend_routes():
    """Test that backend routes are properly defined"""
    LOGGER.info("\n4. Testing backend routes...")
    try:
        from backend.routes import router
        
        routes = [r.path for r in router.routes]
        
        expected_routes = [
            "/api/v1/upload",
            "/api/v1/analyze-trademark",
            "/api/v1/stats",
            "/validate",
        ]
        
        found = sum(1 for r in routes if any(e in r for e in expected_routes))
        
        LOGGER.info(f"   Found {found} expected routes")
        
        assert found >= len(expected_routes) - 1, f"Not all routes found"
        
        LOGGER.info("   ✓ Backend routes test passed")
        return True
    except Exception as e:
        LOGGER.error(f"   ✗ Backend routes test failed: {e}")
        return False

def test_frontend_files():
    """Test that frontend files are properly formatted"""
    LOGGER.info("\n5. Testing frontend files...")
    try:
        base = Path(__file__).parent
        
        # Check App.js
        app_js = base / "frontend" / "src" / "App.js"
        app_content = app_js.read_text()
        
        assert "const API_BASE_URL" in app_content, "Missing API_BASE_URL"
        assert "handleFileSelect" in app_content, "Missing handleFileSelect"
        assert "handleUpload" in app_content, "Missing handleUpload"
        
        # Check UploadForm.js
        upload_js = base / "frontend" / "src" / "components" / "UploadForm.js"
        upload_content = upload_js.read_text()
        
        assert "function UploadForm" in upload_content or "const UploadForm" in upload_content, "Missing UploadForm component"
        assert "drag-and-drop" in upload_content or "dragover" in upload_content, "Missing drag-drop support"
        
        # Check ResultsGrid.js
        results_js = base / "frontend" / "src" / "components" / "ResultsGrid.js"
        results_content = results_js.read_text()
        
        assert "function ResultsGrid" in results_content or "const ResultsGrid" in results_content, "Missing ResultsGrid component"
        assert "collision_risk" in results_content, "Missing risk display"
        
        LOGGER.info("   ✓ Frontend files test passed")
        return True
    except Exception as e:
        LOGGER.error(f"   ✗ Frontend files test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    LOGGER.info("\n" + "="*70)
    LOGGER.info("AI TRADEMARK COLLISION DETECTION - QUICK SMOKE TEST")
    LOGGER.info("="*70)
    
    tests = [
        ("Imports", test_imports),
        ("Dataset Structure", test_dataset_structure),
        ("File Moves", test_file_moves),
        ("Backend Routes", test_backend_routes),
        ("Frontend Files", test_frontend_files),
    ]
    
    results = {}
    for name, test_func in tests:
        results[name] = test_func()
    
    # Summary
    LOGGER.info("\n" + "="*70)
    LOGGER.info("SMOKE TEST SUMMARY")
    LOGGER.info("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, passed_flag in results.items():
        status = "✓" if passed_flag else "✗"
        LOGGER.info(f"{status} {name}")
    
    LOGGER.info("="*70)
    LOGGER.info(f"TOTAL: {passed}/{total} tests passed\n")
    
    return passed == total

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
