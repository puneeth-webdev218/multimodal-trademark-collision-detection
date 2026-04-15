"""
Generate embeddings for all trademark images in the dataset
Saves embeddings and metadata for fast similarity search
"""

import os
import pickle
import numpy as np
from tqdm import tqdm
from feature_extractor import FeatureExtractor


class EmbeddingGenerator:
    """
    Generate and manage embeddings for trademark dataset
    """
    
    def __init__(self, dataset_path, model_name='resnet50'):
        """
        Initialize embedding generator
        
        Args:
            dataset_path (str): Path to trademark images directory
            model_name (str): Model architecture to use
        """
        self.dataset_path = dataset_path
        self.model_name = model_name
        self.extractor = FeatureExtractor(model_name=model_name)
        self.embeddings = []
        self.image_paths = []
        self.image_names = []
        
    def collect_image_paths(self):
        """
        Collect all valid image paths from dataset directory
        
        Returns:
            list: List of image file paths
        """
        supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp')
        image_paths = []
        
        print(f"Scanning directory: {self.dataset_path}")
        
        # Walk through all subdirectories
        for root, dirs, files in os.walk(self.dataset_path):
            for file in files:
                if file.lower().endswith(supported_formats):
                    full_path = os.path.join(root, file)
                    image_paths.append(full_path)
        
        print(f"Found {len(image_paths)} images")
        return image_paths
    
    def generate_embeddings(self, save_path='embeddings.pkl', batch_size=32):
        """
        Generate embeddings for all images and save to disk
        
        Args:
            save_path (str): Path to save embeddings
            batch_size (int): Number of images to process at once
        """
        # Collect all image paths
        image_paths = self.collect_image_paths()
        
        if not image_paths:
            print("No images found in dataset directory!")
            return
        
        print(f"Generating embeddings for {len(image_paths)} images...")
        
        embeddings = []
        valid_paths = []
        valid_names = []
        
        # Process images with progress bar
        for img_path in tqdm(image_paths, desc="Extracting features"):
            features = self.extractor.extract_features(img_path)
            
            if features is not None:
                embeddings.append(features)
                valid_paths.append(img_path)
                valid_names.append(os.path.basename(img_path))
        
        # Convert to numpy array
        embeddings = np.array(embeddings)
        
        print(f"Successfully generated {len(embeddings)} embeddings")
        print(f"Embedding shape: {embeddings.shape}")
        
        # Prepare data to save
        embedding_data = {
            'embeddings': embeddings,
            'image_paths': valid_paths,
            'image_names': valid_names,
            'model_name': self.model_name,
            'embedding_dim': embeddings.shape[1]
        }
        
        # Save to pickle file
        with open(save_path, 'wb') as f:
            pickle.dump(embedding_data, f)
        
        print(f"Embeddings saved to {save_path}")
        
        self.embeddings = embeddings
        self.image_paths = valid_paths
        self.image_names = valid_names
        
        return embedding_data
    
    def load_embeddings(self, load_path='embeddings.pkl'):
        """
        Load embeddings from disk
        
        Args:
            load_path (str): Path to embeddings file
            
        Returns:
            dict: Embedding data
        """
        if not os.path.exists(load_path):
            print(f"Embeddings file {load_path} not found!")
            return None
        
        with open(load_path, 'rb') as f:
            embedding_data = pickle.load(f)
        
        self.embeddings = embedding_data['embeddings']
        self.image_paths = embedding_data['image_paths']
        self.image_names = embedding_data['image_names']
        
        print(f"Loaded {len(self.embeddings)} embeddings from {load_path}")
        print(f"Embedding dimension: {embedding_data['embedding_dim']}")
        
        return embedding_data
    
    def add_new_trademark(self, image_path, embeddings_path='embeddings.pkl'):
        """
        Add a new trademark to existing embeddings
        
        Args:
            image_path (str): Path to new trademark image
            embeddings_path (str): Path to embeddings file
        """
        # Load existing embeddings
        embedding_data = self.load_embeddings(embeddings_path)
        
        if embedding_data is None:
            print("No existing embeddings found. Creating new database...")
            self.embeddings = []
            self.image_paths = []
            self.image_names = []
        
        # Extract features for new image
        print(f"Processing new trademark: {image_path}")
        features = self.extractor.extract_features(image_path)
        
        if features is None:
            print("Failed to extract features from new image!")
            return False
        
        # Add to existing data
        self.embeddings = np.vstack([self.embeddings, features])
        self.image_paths.append(image_path)
        self.image_names.append(os.path.basename(image_path))
        
        # Save updated embeddings
        updated_data = {
            'embeddings': self.embeddings,
            'image_paths': self.image_paths,
            'image_names': self.image_names,
            'model_name': self.model_name,
            'embedding_dim': self.embeddings.shape[1]
        }
        
        with open(embeddings_path, 'wb') as f:
            pickle.dump(updated_data, f)
        
        print(f"Successfully added new trademark. Total: {len(self.embeddings)}")
        return True


def generate_sample_embeddings():
    """
    Generate embeddings for sample dataset
    This is the main function to run for creating the embedding database
    """
    # Configuration
    DATASET_PATH = "../dataset/trademarks"
    OUTPUT_PATH = "embeddings.pkl"
    MODEL_NAME = "resnet50"
    
    # Check if dataset exists
    if not os.path.exists(DATASET_PATH):
        print(f"Dataset directory not found: {DATASET_PATH}")
        print("Please add trademark images to the dataset/trademarks folder")
        return
    
    # Create embedding generator
    generator = EmbeddingGenerator(
        dataset_path=DATASET_PATH,
        model_name=MODEL_NAME
    )
    
    # Generate and save embeddings
    embedding_data = generator.generate_embeddings(
        save_path=OUTPUT_PATH,
        batch_size=32
    )
    
    if embedding_data:
        print("\n" + "="*60)
        print("EMBEDDING GENERATION COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Total images processed: {len(embedding_data['image_names'])}")
        print(f"Embedding dimension: {embedding_data['embedding_dim']}")
        print(f"Model used: {embedding_data['model_name']}")
        print(f"Output file: {OUTPUT_PATH}")
        print("="*60)
    

if __name__ == "__main__":
    generate_sample_embeddings()
