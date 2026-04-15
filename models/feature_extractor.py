"""
Feature Extraction Model using ResNet50
Extracts deep features from trademark/logo images
"""

import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import numpy as np


class FeatureExtractor:
    """
    CNN-based feature extractor using pretrained ResNet50
    Removes the final classification layer to use as embedding generator
    """
    
    def __init__(self, model_name='resnet50', device=None):
        """
        Initialize the feature extractor
        
        Args:
            model_name (str): Name of the pretrained model ('resnet50', 'resnet101')
            device (str): 'cuda' or 'cpu'
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        self.model_name = model_name
        self.model = self._load_model()
        self.transform = self._get_transforms()
        
    def _load_model(self):
        """
        Load pretrained ResNet50 and remove final classification layer
        
        Returns:
            model: Feature extraction model
        """
        print(f"Loading {self.model_name} model...")
        
        if self.model_name == 'resnet50':
            # Load pretrained ResNet50 (using modern weights API)
            model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
            self.embedding_dim = 2048
        elif self.model_name == 'resnet101':
            model = models.resnet101(weights=models.ResNet101_Weights.IMAGENET1K_V2)
            self.embedding_dim = 2048
        elif self.model_name == 'efficientnet_b0':
            model = models.efficientnet_b0(weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1)
            self.embedding_dim = 1280
        elif self.model_name == 'efficientnet_b4':
            model = models.efficientnet_b4(weights=models.EfficientNet_B4_Weights.IMAGENET1K_V1)
            self.embedding_dim = 1792
        elif self.model_name == 'vgg16':
            model = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)
            self.embedding_dim = 4096
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")
        
        # Remove the final fully connected layer
        # For ResNet, this gives us 2048-dimensional features
        if 'resnet' in self.model_name:
            model = nn.Sequential(*list(model.children())[:-1])
        elif 'efficientnet' in self.model_name:
            model.classifier = nn.Identity()
        elif 'vgg' in self.model_name:
            model.classifier = nn.Sequential(*list(model.classifier.children())[:-1])
        
        model = model.to(self.device)
        model.eval()  # Set to evaluation mode
        
        print(f"Model loaded successfully on {self.device}")
        return model
    
    def _get_transforms(self):
        """
        Define image preprocessing pipeline
        
        Returns:
            transforms: PyTorch transforms
        """
        transform = transforms.Compose([
            transforms.Resize((224, 224)),  # Resize to 224x224
            transforms.ToTensor(),  # Convert to tensor
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],  # ImageNet mean
                std=[0.229, 0.224, 0.225]     # ImageNet std
            )
        ])
        return transform
    
    def extract_features(self, image_path):
        """
        Extract feature vector from an image
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            numpy.ndarray: Feature vector (2048-dimensional for ResNet50)
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_tensor = self.transform(image).unsqueeze(0)  # Add batch dimension
            image_tensor = image_tensor.to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.model(image_tensor)
            
            # Flatten and convert to numpy
            features = features.squeeze().cpu().numpy()
            
            # Normalize the feature vector (L2 normalization)
            features = features / np.linalg.norm(features)
            
            return features
            
        except Exception as e:
            print(f"Error extracting features from {image_path}: {str(e)}")
            return None
    
    def extract_features_batch(self, image_paths, batch_size=32):
        """
        Extract features from multiple images in batches
        
        Args:
            image_paths (list): List of image file paths
            batch_size (int): Number of images to process at once
            
        Returns:
            numpy.ndarray: Array of feature vectors
        """
        all_features = []
        
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i:i + batch_size]
            batch_images = []
            
            # Load and preprocess batch
            for path in batch_paths:
                try:
                    image = Image.open(path).convert('RGB')
                    image_tensor = self.transform(image)
                    batch_images.append(image_tensor)
                except Exception as e:
                    print(f"Error loading {path}: {str(e)}")
                    continue
            
            if not batch_images:
                continue
            
            # Stack into batch tensor
            batch_tensor = torch.stack(batch_images).to(self.device)
            
            # Extract features
            with torch.no_grad():
                features = self.model(batch_tensor)
            
            # Process features
            features = features.squeeze().cpu().numpy()
            
            # Normalize each feature vector
            if len(features.shape) == 1:  # Single image
                features = features / np.linalg.norm(features)
                all_features.append(features)
            else:  # Multiple images
                for feat in features:
                    feat = feat / np.linalg.norm(feat)
                    all_features.append(feat)
        
        return np.array(all_features)


def load_model(model_name='resnet50', device=None):
    """
    Convenience function to load a feature extractor
    
    Args:
        model_name (str): Model architecture to use
        device (str): Device to load model on
        
    Returns:
        FeatureExtractor: Initialized feature extractor
    """
    return FeatureExtractor(model_name=model_name, device=device)


if __name__ == "__main__":
    # Test the feature extractor
    print("Testing Feature Extractor...")
    
    extractor = load_model()
    print(f"Model: {extractor.model_name}")
    print(f"Device: {extractor.device}")
    
    # Test with a sample image (you need to provide an actual image)
    # features = extractor.extract_features("sample_image.jpg")
    # print(f"Feature vector shape: {features.shape}")
    # print(f"Feature vector (first 10 values): {features[:10]}")
