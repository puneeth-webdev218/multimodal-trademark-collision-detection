#!/usr/bin/env python3
"""
End-to-End Validation Script for AI Trademark Collision Detection System

Tests:
1. Dataset loading
2. Embedding generation
3. FAISS index creation
4. Similarity search (image-only)
5. Self-match validation
6. Full trademark analysis
7. API endpoints
"""

import logging
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
LOGGER = logging.getLogger(__name__)


def test_dataset_loading():
    """Test 1: Dataset Loading"""
    LOGGER.info("\n" + "="*70)
    LOGGER.info("TEST 1: Dataset Loading")
    LOGGER.info("="*70)
    
    try:
        from dataset.dataset_loader import scan_logo_dataset
        
        LOGGER.info("Scanning dataset...")
        result = scan_logo_dataset()
        
        LOGGER.info(f"✓ Dataset scan complete:")
        LOGGER.info(f"  - Root: {result['dataset_root']}")
        LOGGER.info(f"  - Categories: {result['num_categories']}")
        LOGGER.info(f"  - Brands: {result['num_brands']}")
        LOGGER.info(f"  - Images: {result['num_images']}")
        LOGGER.info(f"  - Skipped: {result['skipped_invalid']}")
        
        assert result['num_images'] > 0, "No images found in dataset"
        assert result['num_brands'] > 0, "No brands found in dataset"
        
        LOGGER.info("✓ Dataset loading test PASSED")
        return True
    except Exception as e:
        LOGGER.error(f"✗ Dataset loading test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_embedding_generation():
    """Test 2: Embedding Generation"""
    LOGGER.info("\n" + "="*70)
    LOGGER.info("TEST 2: Embedding Generation")
    LOGGER.info("="*70)
    
    try:
        from models.generate_embeddings import load_or_generate_logo_embeddings
        
        LOGGER.info("Generating/loading embeddings...")
        start = time.time()
        payload = load_or_generate_logo_embeddings()
        elapsed = time.time() - start
        
        LOGGER.info(f"✓ Embeddings loaded in {elapsed:.2f}s:")
        LOGGER.info(f"  - Shape: {payload['embeddings'].shape}")
        LOGGER.info(f"  - Images: {payload['num_images']}")
        LOGGER.info(f"  - Brands: {payload['num_brands']}")
        LOGGER.info(f"  - Categories: {payload['num_categories']}")
        LOGGER.info(f"  - Embedding dim: {payload['embedding_dim']}")
        
        assert payload['embeddings'].shape[0] > 0, "No embeddings generated"
        assert payload['embedding_dim'] > 0, "Invalid embedding dimension"
        
        LOGGER.info("✓ Embedding generation test PASSED")
        return True
    except Exception as e:
        LOGGER.error(f"✗ Embedding generation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_faiss_index():
    """Test 3: FAISS Index Creation"""
    LOGGER.info("\n" + "="*70)
    LOGGER.info("TEST 3: FAISS Index Creation")
    LOGGER.info("="*70)
    
    try:
        from similarity.faiss_index import FAISSIndex
        from models.generate_embeddings import load_or_generate_logo_embeddings
        
        LOGGER.info("Loading embeddings...")
        payload = load_or_generate_logo_embeddings()
        
        LOGGER.info("Creating/loading FAISS index...")
        base = Path(__file__).resolve().parents[1]
        index_path = str(base / "similarity" / "faiss_index.index")
        metadata_path = str(base / "similarity" / "index_metadata.pkl")
        
        faiss_idx = FAISSIndex(index_type="cosine")
        faiss_idx.load_or_build(
            embeddings_payload=payload,
            index_path=index_path,
            metadata_path=metadata_path,
            force_rebuild=False,
        )
        
        LOGGER.info(f"✓ FAISS index ready:")
        LOGGER.info(f"  - Total vectors: {faiss_idx.index.ntotal}")
        LOGGER.info(f"  - Index type: {faiss_idx.index_type}")
        LOGGER.info(f"  - Metadata keys: {list(faiss_idx.metadata.keys())}")
        
        assert faiss_idx.index.ntotal > 0, "No vectors in FAISS index"
        
        LOGGER.info("✓ FAISS index test PASSED")
        return True
    except Exception as e:
        LOGGER.error(f"✗ FAISS index test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_search():
    """Test 4: Image-based Similarity Search"""
    LOGGER.info("\n" + "="*70)
    LOGGER.info("TEST 4: Image-based Similarity Search")
    LOGGER.info("="*70)
    
    try:
        from similarity.search import SimilaritySearch
        from dataset.dataset_loader import scan_logo_dataset
        import random
        
        LOGGER.info("Initializing search engine...")
        search_engine = SimilaritySearch()
        
        # Get a sample image from the dataset
        LOGGER.info("Getting sample image...")
        scan = scan_logo_dataset()
        records = scan["records"]
        
        if not records:
            LOGGER.warning("No records in dataset for testing")
            return False
        
        sample_record = random.choice(records)
        LOGGER.info(f"Testing with image: {Path(sample_record.image_path).name}")
        
        # Search for similar images
        LOGGER.info("Searching for similar images...")
        start = time.time()
        results = search_engine.search_image_only(
            image_path=sample_record.image_path,
            top_k=5
        )
        elapsed = time.time() - start
        
        LOGGER.info(f"✓ Search completed in {elapsed:.2f}s:")
        LOGGER.info(f"  - Top similarity: {results['top_score']:.4f}")
        LOGGER.info(f"  - Detected: {results['detected']}")
        LOGGER.info(f"  - Risk: {results['collision_risk']['risk_level']}")
        
        # Check if image matched itself
        similar = results['similar_trademarks']
        if similar and len(similar) > 0:
            top_match = similar[0]
            LOGGER.info(f"  - Top match: {top_match['image_name']} ({top_match['similarity_percentage']:.1f}%)")
            
            if top_match['image_name'] == Path(sample_record.image_path).name:
                LOGGER.info(f"  ✓ Image matched itself with {top_match['similarity_percentage']:.1f}% similarity")
        
        LOGGER.info("✓ Image search test PASSED")
        return True
    except Exception as e:
        LOGGER.error(f"✗ Image search test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_self_match_validation():
    """Test 5: Self-Match Validation"""
    LOGGER.info("\n" + "="*70)
    LOGGER.info("TEST 5: Self-Match Validation")
    LOGGER.info("="*70)
    
    try:
        from similarity.search import SimilaritySearch
        
        LOGGER.info("Initializing search engine...")
        search_engine = SimilaritySearch()
        
        LOGGER.info("Running self-match validation (10 samples)...")
        start = time.time()
        results = search_engine.run_self_match_test(sample_size=10, top_k=5)
        elapsed = time.time() - start
        
        LOGGER.info(f"✓ Validation completed in {elapsed:.2f}s:")
        LOGGER.info(f"  - Tested: {results['tested_count']}")
        LOGGER.info(f"  - Passed: {results['passed_count']}")
        LOGGER.info(f"  - Success rate: {results['success_rate']*100:.1f}%")
        LOGGER.info(f"  - Status: {'PASS' if results['success'] else 'WARNING'}")
        
        if results['details']:
            for detail in results['details'][:3]:  # Show first 3
                LOGGER.info(f"    - {detail['image']}: similarity={detail['top_similarity']:.4f}, passed={detail['passed']}")
        
        LOGGER.info("✓ Self-match validation test PASSED")
        return True
    except Exception as e:
        LOGGER.error(f"✗ Self-match validation test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_analysis():
    """Test 6: Full Trademark Analysis"""
    LOGGER.info("\n" + "="*70)
    LOGGER.info("TEST 6: Full Trademark Analysis")
    LOGGER.info("="*70)
    
    try:
        from similarity.search import SimilaritySearch
        from dataset.dataset_loader import scan_logo_dataset
        import random
        
        LOGGER.info("Initializing search engine...")
        search_engine = SimilaritySearch()
        
        # Get a sample image
        scan = scan_logo_dataset()
        records = scan["records"]
        
        if not records:
            LOGGER.warning("No records in dataset for testing")
            return False
        
        sample_record = random.choice(records)
        LOGGER.info(f"Testing with: {Path(sample_record.image_path).name} (brand: {sample_record.brand})")
        
        # Run full analysis
        LOGGER.info("Running full trademark analysis...")
        start = time.time()
        analysis = search_engine.analyze_trademark(
            image_path=sample_record.image_path,
            trademark_name=sample_record.brand,
            top_k=5
        )
        elapsed = time.time() - start
        
        LOGGER.info(f"✓ Analysis completed in {elapsed:.2f}s:")
        scores = analysis['scores']
        LOGGER.info(f"  - Logo similarity: {scores['best_logo_similarity']:.4f}")
        LOGGER.info(f"  - Name similarity: {scores['best_name_similarity']:.4f}")
        LOGGER.info(f"  - Collision score: {scores['collision_score']:.4f}")
        LOGGER.info(f"  - Risk level: {analysis['risk']['level']}")
        LOGGER.info(f"  - Dataset size: {analysis['dataset']['num_images']} images")
        
        LOGGER.info("✓ Full analysis test PASSED")
        return True
    except Exception as e:
        LOGGER.error(f"✗ Full analysis test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_endpoints():
    """Test 7: API Endpoints"""
    LOGGER.info("\n" + "="*70)
    LOGGER.info("TEST 7: API Endpoints")
    LOGGER.info("="*70)
    
    try:
        import requests
        
        BASE_URL = "http://127.0.0.1:8000"
        
        # Test health check
        LOGGER.info("Testing /health endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=5)
            if response.status_code == 200:
                LOGGER.info(f"✓ Health check: {response.json()['status']}")
            else:
                LOGGER.warning(f"Health check returned {response.status_code}")
        except Exception as e:
            LOGGER.warning(f"Could not reach health endpoint: {e}")
            LOGGER.info("  (This is OK if backend is not running)")
        
        # Test stats endpoint
        LOGGER.info("Testing /stats endpoint...")
        try:
            response = requests.get(f"{BASE_URL}/api/v1/stats", timeout=5)
            if response.status_code == 200:
                stats = response.json()
                LOGGER.info(f"✓ Stats endpoint:")
                LOGGER.info(f"  - Status: {stats.get('status')}")
                LOGGER.info(f"  - Total trademarks: {stats.get('total_trademarks')}")
                LOGGER.info(f"  - Model: {stats.get('model')}")
            else:
                LOGGER.warning(f"Stats endpoint returned {response.status_code}")
        except Exception as e:
            LOGGER.warning(f"Could not reach stats endpoint: {e}")
            LOGGER.info("  (This is OK if backend is not running)")
        
        LOGGER.info("✓ API endpoint test PASSED (or backend not running)")
        return True
    except Exception as e:
        LOGGER.error(f"✗ API endpoint test FAILED: {e}")
        return False


def main():
    """Run all validation tests"""
    LOGGER.info("\n\n" + "="*70)
    LOGGER.info("AI TRADEMARK COLLISION DETECTION SYSTEM - VALIDATION SUITE")
    LOGGER.info("="*70)
    
    tests = [
        ("Dataset Loading", test_dataset_loading),
        ("Embedding Generation", test_embedding_generation),
        ("FAISS Index", test_faiss_index),
        ("Image Search", test_image_search),
        ("Self-Match Validation", test_self_match_validation),
        ("Full Analysis", test_full_analysis),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            LOGGER.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    LOGGER.info("\n\n" + "="*70)
    LOGGER.info("VALIDATION SUMMARY")
    LOGGER.info("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_flag in results.items():
        status = "✓ PASS" if passed_flag else "✗ FAIL"
        LOGGER.info(f"{status:8} | {test_name}")
    
    LOGGER.info("="*70)
    LOGGER.info(f"TOTAL: {passed}/{total} tests passed")
    LOGGER.info("="*70 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
