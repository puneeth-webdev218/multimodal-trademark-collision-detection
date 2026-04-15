"""
Evaluation Metrics for Trademark Collision Detection
Measures the performance of the similarity search system
"""

import numpy as np
from typing import List, Dict, Tuple
import os
import sys
from collections import defaultdict

sys.path.append(os.path.join(os.path.dirname(__file__), '../similarity'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../models'))


def precision_at_k(relevant_items: List[str], retrieved_items: List[str], k: int) -> float:
    """
    Calculate Precision@K
    
    Args:
        relevant_items: List of ground truth relevant item IDs
        retrieved_items: List of retrieved item IDs (ranked)
        k: Number of top items to consider
        
    Returns:
        Precision@K score
    """
    if k <= 0:
        return 0.0
    
    relevant_set = set(relevant_items)
    retrieved_at_k = retrieved_items[:k]
    
    relevant_retrieved = len(set(retrieved_at_k) & relevant_set)
    
    return relevant_retrieved / k


def recall_at_k(relevant_items: List[str], retrieved_items: List[str], k: int) -> float:
    """
    Calculate Recall@K
    
    Args:
        relevant_items: List of ground truth relevant item IDs
        retrieved_items: List of retrieved item IDs (ranked)
        k: Number of top items to consider
        
    Returns:
        Recall@K score
    """
    if len(relevant_items) == 0:
        return 0.0
    
    relevant_set = set(relevant_items)
    retrieved_at_k = retrieved_items[:k]
    
    relevant_retrieved = len(set(retrieved_at_k) & relevant_set)
    
    return relevant_retrieved / len(relevant_set)


def average_precision(relevant_items: List[str], retrieved_items: List[str]) -> float:
    """
    Calculate Average Precision for a single query
    
    Args:
        relevant_items: List of ground truth relevant item IDs
        retrieved_items: List of retrieved item IDs (ranked)
        
    Returns:
        Average Precision score
    """
    if len(relevant_items) == 0:
        return 0.0
    
    relevant_set = set(relevant_items)
    
    precisions = []
    relevant_count = 0
    
    for i, item in enumerate(retrieved_items):
        if item in relevant_set:
            relevant_count += 1
            precisions.append(relevant_count / (i + 1))
    
    if len(precisions) == 0:
        return 0.0
    
    return sum(precisions) / len(relevant_items)


def mean_average_precision(queries_results: List[Tuple[List[str], List[str]]]) -> float:
    """
    Calculate Mean Average Precision (mAP) across multiple queries
    
    Args:
        queries_results: List of (relevant_items, retrieved_items) tuples
        
    Returns:
        mAP score
    """
    if len(queries_results) == 0:
        return 0.0
    
    aps = [average_precision(rel, ret) for rel, ret in queries_results]
    return sum(aps) / len(aps)


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def euclidean_distance(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate Euclidean distance between two vectors
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Euclidean distance
    """
    return np.linalg.norm(vec1 - vec2)


def top_k_accuracy(predictions: List[List[str]], ground_truth: List[str], k: int) -> float:
    """
    Calculate Top-K Accuracy
    
    Args:
        predictions: List of predicted item lists (ranked)
        ground_truth: List of correct item IDs
        k: Number of top predictions to consider
        
    Returns:
        Top-K accuracy score
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("Predictions and ground truth must have same length")
    
    correct = 0
    for pred_list, true_item in zip(predictions, ground_truth):
        if true_item in pred_list[:k]:
            correct += 1
    
    return correct / len(predictions)


class EvaluationMetrics:
    """
    Comprehensive evaluation metrics for trademark similarity
    """
    
    def __init__(self):
        self.results = []
        
    def add_query_result(self, query_id: str, relevant: List[str], retrieved: List[str]):
        """Add a single query result for evaluation"""
        self.results.append({
            'query_id': query_id,
            'relevant': relevant,
            'retrieved': retrieved
        })
    
    def compute_metrics(self, k_values: List[int] = [1, 3, 5, 10]) -> Dict:
        """
        Compute all evaluation metrics
        
        Args:
            k_values: List of K values for Precision@K and Recall@K
            
        Returns:
            Dictionary of computed metrics
        """
        metrics = {}
        
        # Precision@K and Recall@K
        for k in k_values:
            precisions = []
            recalls = []
            
            for result in self.results:
                p = precision_at_k(result['relevant'], result['retrieved'], k)
                r = recall_at_k(result['relevant'], result['retrieved'], k)
                precisions.append(p)
                recalls.append(r)
            
            metrics[f'precision@{k}'] = np.mean(precisions)
            metrics[f'recall@{k}'] = np.mean(recalls)
        
        # Mean Average Precision
        query_pairs = [(r['relevant'], r['retrieved']) for r in self.results]
        metrics['mAP'] = mean_average_precision(query_pairs)
        
        # Average number of relevant items found
        avg_relevant_found = np.mean([
            len(set(r['retrieved']) & set(r['relevant'])) 
            for r in self.results
        ])
        metrics['avg_relevant_found'] = avg_relevant_found
        
        return metrics
    
    def print_report(self):
        """Print formatted evaluation report"""
        metrics = self.compute_metrics()
        
        print("=" * 60)
        print("EVALUATION METRICS REPORT")
        print("=" * 60)
        print(f"\nTotal Queries: {len(self.results)}")
        print("\n--- Precision & Recall ---")
        for k in [1, 3, 5, 10]:
            if f'precision@{k}' in metrics:
                print(f"  Precision@{k}: {metrics[f'precision@{k}']:.4f}")
                print(f"  Recall@{k}:    {metrics[f'recall@{k}']:.4f}")
        
        print("\n--- Mean Average Precision ---")
        print(f"  mAP: {metrics['mAP']:.4f}")
        
        print("\n--- Additional Metrics ---")
        print(f"  Avg Relevant Found: {metrics['avg_relevant_found']:.2f}")
        print("=" * 60)
        
        return metrics


def evaluate_similarity_distribution(embeddings: np.ndarray, labels: List[str] = None):
    """
    Analyze the distribution of similarity scores
    
    Args:
        embeddings: Array of embedding vectors (N x D)
        labels: Optional labels for each embedding
        
    Returns:
        Dictionary of distribution statistics
    """
    n_samples = len(embeddings)
    
    # Calculate pairwise similarities
    similarities = []
    
    for i in range(n_samples):
        for j in range(i + 1, n_samples):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)
    
    similarities = np.array(similarities)
    
    stats = {
        'mean_similarity': np.mean(similarities),
        'std_similarity': np.std(similarities),
        'min_similarity': np.min(similarities),
        'max_similarity': np.max(similarities),
        'median_similarity': np.median(similarities),
        'percentile_25': np.percentile(similarities, 25),
        'percentile_75': np.percentile(similarities, 75),
        'percentile_90': np.percentile(similarities, 90),
        'percentile_95': np.percentile(similarities, 95)
    }
    
    return stats


if __name__ == "__main__":
    # Example usage
    print("Evaluation Metrics Demo")
    print("=" * 60)
    
    # Create sample evaluation
    evaluator = EvaluationMetrics()
    
    # Add sample results (in real scenario, these would come from actual queries)
    evaluator.add_query_result(
        query_id="logo1",
        relevant=["similar1", "similar2", "similar3"],
        retrieved=["similar1", "unknown1", "similar2", "unknown2", "similar3"]
    )
    
    evaluator.add_query_result(
        query_id="logo2",
        relevant=["brand1", "brand2"],
        retrieved=["brand1", "brand2", "other1", "other2", "other3"]
    )
    
    # Print report
    evaluator.print_report()
