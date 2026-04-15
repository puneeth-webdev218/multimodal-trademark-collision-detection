"""
Similarity search package for AI Trademark Collision Detection
"""

from .faiss_index import FAISSIndex, build_index_from_embeddings
from .search import SimilaritySearch

__all__ = ['FAISSIndex', 'build_index_from_embeddings', 'SimilaritySearch']
