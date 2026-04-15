"""
FAISS Index Builder for Fast Similarity Search
Creates and manages FAISS index for efficient nearest neighbor search
"""

import numpy as np
import faiss
import pickle
import os


class FAISSIndex:
    """
    FAISS-based similarity search index
    Supports fast nearest neighbor search for trademark embeddings
    """
    
    def __init__(self, dimension=2048, index_type='L2'):
        """
        Initialize FAISS index
        
        Args:
            dimension (int): Dimension of embedding vectors
            index_type (str): 'L2' for Euclidean distance or 'cosine' for cosine similarity
        """
        self.dimension = dimension
        self.index_type = index_type
        self.index = None
        self.image_paths = []
        self.image_names = []
        
    def build_index(self, embeddings, image_paths, image_names, use_gpu=False):
        """
        Build FAISS index from embeddings
        
        Args:
            embeddings (numpy.ndarray): Array of embedding vectors (N x D)
            image_paths (list): List of image file paths
            image_names (list): List of image filenames
            use_gpu (bool): Whether to use GPU for indexing
        """
        print(f"Building FAISS index with {len(embeddings)} vectors...")
        
        self.image_paths = image_paths
        self.image_names = image_names
        
        # Ensure embeddings are float32
        embeddings = embeddings.astype('float32')
        
        # Create appropriate index type
        if self.index_type == 'cosine':
            # For cosine similarity, normalize vectors and use inner product
            faiss.normalize_L2(embeddings)
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner Product (cosine)
        else:
            # L2 (Euclidean) distance
            self.index = faiss.IndexFlatL2(self.dimension)
        
        # Use GPU if requested and available
        if use_gpu and faiss.get_num_gpus() > 0:
            print("Using GPU for FAISS indexing")
            res = faiss.StandardGpuResources()
            self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
        
        # Add vectors to index
        self.index.add(embeddings)
        
        print(f"Index built successfully with {self.index.ntotal} vectors")
        
    def save_index(self, index_path='faiss_index.bin', metadata_path='index_metadata.pkl'):
        """
        Save FAISS index and metadata to disk
        
        Args:
            index_path (str): Path to save FAISS index
            metadata_path (str): Path to save metadata
        """
        # Save FAISS index
        if self.index is not None:
            # Convert GPU index to CPU for saving
            if hasattr(self.index, 'index'):
                cpu_index = faiss.index_gpu_to_cpu(self.index)
            else:
                cpu_index = self.index
            
            faiss.write_index(cpu_index, index_path)
            print(f"FAISS index saved to {index_path}")
        
        # Save metadata
        metadata = {
            'image_paths': self.image_paths,
            'image_names': self.image_names,
            'dimension': self.dimension,
            'index_type': self.index_type
        }
        
        with open(metadata_path, 'wb') as f:
            pickle.dump(metadata, f)
        
        print(f"Metadata saved to {metadata_path}")
    
    def load_index(self, index_path='faiss_index.bin', metadata_path='index_metadata.pkl', use_gpu=False):
        """
        Load FAISS index and metadata from disk
        
        Args:
            index_path (str): Path to FAISS index file
            metadata_path (str): Path to metadata file
            use_gpu (bool): Whether to load index on GPU
        """
        # Load FAISS index
        if os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            
            # Move to GPU if requested
            if use_gpu and faiss.get_num_gpus() > 0:
                res = faiss.StandardGpuResources()
                self.index = faiss.index_cpu_to_gpu(res, 0, self.index)
            
            print(f"FAISS index loaded from {index_path}")
            print(f"Index contains {self.index.ntotal} vectors")
        else:
            print(f"Index file {index_path} not found!")
            return False
        
        # Load metadata
        if os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                metadata = pickle.load(f)
            
            self.image_paths = metadata['image_paths']
            self.image_names = metadata['image_names']
            self.dimension = metadata['dimension']
            self.index_type = metadata['index_type']
            
            print(f"Metadata loaded: {len(self.image_names)} images")
        else:
            print(f"Metadata file {metadata_path} not found!")
            return False
        
        return True
    
    def add_to_index(self, embeddings, image_paths, image_names):
        """
        Add new embeddings to existing index
        
        Args:
            embeddings (numpy.ndarray): New embedding vectors
            image_paths (list): New image paths
            image_names (list): New image names
        """
        if self.index is None:
            print("Index not initialized! Build or load an index first.")
            return
        
        embeddings = embeddings.astype('float32')
        
        if self.index_type == 'cosine':
            faiss.normalize_L2(embeddings)
        
        self.index.add(embeddings)
        self.image_paths.extend(image_paths)
        self.image_names.extend(image_names)
        
        print(f"Added {len(embeddings)} vectors. Total: {self.index.ntotal}")


def build_index_from_embeddings(embeddings_path='../models/embeddings.pkl', 
                                 output_index='faiss_index.bin',
                                 output_metadata='index_metadata.pkl',
                                 use_gpu=False):
    """
    Build FAISS index from saved embeddings
    
    Args:
        embeddings_path (str): Path to embeddings pickle file
        output_index (str): Path to save FAISS index
        output_metadata (str): Path to save metadata
        use_gpu (bool): Whether to use GPU
    """
    print("="*60)
    print("BUILDING FAISS INDEX")
    print("="*60)
    
    # Load embeddings
    if not os.path.exists(embeddings_path):
        print(f"Embeddings file not found: {embeddings_path}")
        return None
    
    with open(embeddings_path, 'rb') as f:
        embedding_data = pickle.load(f)
    
    embeddings = embedding_data['embeddings']
    image_paths = embedding_data['image_paths']
    image_names = embedding_data['image_names']
    dimension = embedding_data['embedding_dim']
    
    print(f"Loaded {len(embeddings)} embeddings of dimension {dimension}")
    
    # Create FAISS index
    faiss_index = FAISSIndex(dimension=dimension, index_type='cosine')
    
    # Build index
    faiss_index.build_index(
        embeddings=embeddings,
        image_paths=image_paths,
        image_names=image_names,
        use_gpu=use_gpu
    )
    
    # Save index
    faiss_index.save_index(
        index_path=output_index,
        metadata_path=output_metadata
    )
    
    print("="*60)
    print("INDEX BUILT SUCCESSFULLY")
    print("="*60)
    
    return faiss_index


if __name__ == "__main__":
    # Build index from embeddings
    build_index_from_embeddings(
        embeddings_path='../models/embeddings.pkl',
        output_index='faiss_index.bin',
        output_metadata='index_metadata.pkl',
        use_gpu=False
    )
