"""
Similarity Search Engine
Performs fast nearest neighbor search to find similar trademarks
"""

import numpy as np
import faiss
from faiss_index import FAISSIndex
import os
import sys

# Add models directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '../models'))
from feature_extractor import FeatureExtractor


class SimilaritySearch:
    """
    Trademark similarity search engine
    Finds visually similar logos using FAISS and deep learning features
    """
    
    def __init__(self, index_path='faiss_index.bin', 
                 metadata_path='index_metadata.pkl',
                 model_name='resnet50'):
        """
        Initialize similarity search engine
        
        Args:
            index_path (str): Path to FAISS index file
            metadata_path (str): Path to metadata file
            model_name (str): Feature extraction model
        """
        self.faiss_index = FAISSIndex()
        self.feature_extractor = FeatureExtractor(model_name=model_name)
        
        # Load index
        success = self.faiss_index.load_index(index_path, metadata_path)
        if not success:
            print("Warning: Failed to load FAISS index!")
        
    def search_similar(self, query_image_path, top_k=5, return_distances=True):
        """
        Search for similar trademarks
        
        Args:
            query_image_path (str): Path to query trademark image
            top_k (int): Number of similar results to return
            return_distances (bool): Whether to return similarity distances
            
        Returns:
            list: List of similar trademark results with metadata
        """
        # Extract features from query image
        query_features = self.feature_extractor.extract_features(query_image_path)
        
        if query_features is None:
            print(f"Failed to extract features from {query_image_path}")
            return []
        
        # Prepare query vector for FAISS
        query_vector = query_features.reshape(1, -1).astype('float32')
        
        # Normalize if using cosine similarity
        if self.faiss_index.index_type == 'cosine':
            faiss.normalize_L2(query_vector)
        
        # Search FAISS index
        distances, indices = self.faiss_index.index.search(query_vector, top_k + 1)
        
        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.faiss_index.image_names):
                # Convert distance to similarity score (higher is more similar)
                if self.faiss_index.index_type == 'cosine':
                    # For cosine similarity (inner product), higher is better
                    similarity_score = float(dist)  # Already 0-1 range
                else:
                    # For L2 distance, convert to similarity (inverse)
                    similarity_score = 1.0 / (1.0 + float(dist))
                
                result = {
                    'rank': i + 1,
                    'image_name': self.faiss_index.image_names[idx],
                    'image_path': self.faiss_index.image_paths[idx],
                    'similarity_score': similarity_score,
                    'distance': float(dist)
                }
                
                results.append(result)
        
        # Remove the query image itself if it's in the results
        results = [r for r in results if r['image_path'] != query_image_path]
        
        # Return top_k results
        return results[:top_k]
    
    def search_by_features(self, query_features, top_k=5):
        """
        Search using pre-extracted features
        
        Args:
            query_features (numpy.ndarray): Feature vector
            top_k (int): Number of results to return
            
        Returns:
            list: Similar trademark results
        """
        query_vector = query_features.reshape(1, -1).astype('float32')
        
        if self.faiss_index.index_type == 'cosine':
            faiss.normalize_L2(query_vector)
        
        distances, indices = self.faiss_index.index.search(query_vector, top_k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.faiss_index.image_names):
                if self.faiss_index.index_type == 'cosine':
                    similarity_score = float(dist)
                else:
                    similarity_score = 1.0 / (1.0 + float(dist))
                
                result = {
                    'rank': i + 1,
                    'image_name': self.faiss_index.image_names[idx],
                    'image_path': self.faiss_index.image_paths[idx],
                    'similarity_score': similarity_score
                }
                
                results.append(result)
        
        return results
    
    def calculate_collision_risk(self, similarity_score):
        """
        Determine collision risk level based on similarity score
        
        Args:
            similarity_score (float): Similarity score (0-1)
            
        Returns:
            dict: Risk assessment
        """
        if similarity_score >= 0.85:
            risk_level = "HIGH"
            message = "High collision risk - Logo is very similar to existing trademark"
            color = "red"
        elif similarity_score >= 0.70:
            risk_level = "MEDIUM"
            message = "Medium collision risk - Logo has notable similarities"
            color = "orange"
        else:
            risk_level = "LOW"
            message = "Low collision risk - Logo appears sufficiently distinct"
            color = "green"
        
        return {
            'risk_level': risk_level,
            'message': message,
            'color': color,
            'similarity_score': similarity_score
        }
    
    def batch_search(self, query_image_paths, top_k=5):
        """
        Search for multiple query images at once
        
        Args:
            query_image_paths (list): List of query image paths
            top_k (int): Number of results per query
            
        Returns:
            dict: Results for each query image
        """
        results = {}
        
        for img_path in query_image_paths:
            similar = self.search_similar(img_path, top_k)
            results[img_path] = similar
        
        return results
    
    def get_statistics(self):
        """
        Get statistics about the search index
        
        Returns:
            dict: Index statistics
        """
        return {
            'total_trademarks': self.faiss_index.index.ntotal if self.faiss_index.index else 0,
            'embedding_dimension': self.faiss_index.dimension,
            'index_type': self.faiss_index.index_type,
            'model': self.feature_extractor.model_name
        }


def demo_search(query_image):
    """
    Demo function to test similarity search
    
    Args:
        query_image (str): Path to query image
    """
    print("="*60)
    print("TRADEMARK SIMILARITY SEARCH DEMO")
    print("="*60)
    
    # Initialize search engine
    search_engine = SimilaritySearch(
        index_path='faiss_index.bin',
        metadata_path='index_metadata.pkl',
        model_name='resnet50'
    )
    
    # Get statistics
    stats = search_engine.get_statistics()
    print(f"\nIndex Statistics:")
    print(f"  Total Trademarks: {stats['total_trademarks']}")
    print(f"  Embedding Dimension: {stats['embedding_dimension']}")
    print(f"  Similarity Metric: {stats['index_type']}")
    print(f"  Model: {stats['model']}")
    
    # Search for similar trademarks
    print(f"\nSearching for trademarks similar to: {query_image}")
    results = search_engine.search_similar(query_image, top_k=5)
    
    # Display results
    print(f"\nTop {len(results)} Similar Trademarks:")
    print("-" * 60)
    
    for result in results:
        print(f"\nRank {result['rank']}:")
        print(f"  Image: {result['image_name']}")
        print(f"  Similarity Score: {result['similarity_score']:.4f} ({result['similarity_score']*100:.2f}%)")
        
        # Calculate collision risk
        risk = search_engine.calculate_collision_risk(result['similarity_score'])
        print(f"  Risk Level: {risk['risk_level']} - {risk['message']}")
    
    # Overall risk assessment (based on highest similarity)
    if results:
        highest_similarity = max(r['similarity_score'] for r in results)
        overall_risk = search_engine.calculate_collision_risk(highest_similarity)
        
        print("\n" + "="*60)
        print("OVERALL COLLISION RISK ASSESSMENT")
        print("="*60)
        print(f"Risk Level: {overall_risk['risk_level']}")
        print(f"Message: {overall_risk['message']}")
        print("="*60)


if __name__ == "__main__":
    # Test with a sample image
    sample_image = "../uploads/test_logo.jpg"
    
    if os.path.exists(sample_image):
        demo_search(sample_image)
    else:
        print(f"Sample image not found: {sample_image}")
        print("Please provide a test image path.")
