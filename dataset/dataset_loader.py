"""
Dataset Loader for AI Trademark Collision Detection System
Loads, preprocesses, and prepares trademark images for training and inference.
"""

import os
import torch
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import numpy as np
from typing import List, Tuple, Optional
import random


class TrademarkDataset(Dataset):
    """
    PyTorch Dataset for loading trademark/logo images.
    Handles image loading, resizing, and normalization.
    """
    
    def __init__(
        self,
        image_dir: str,
        transform: Optional[transforms.Compose] = None,
        image_size: Tuple[int, int] = (224, 224)
    ):
        """
        Initialize the dataset.
        
        Args:
            image_dir: Directory containing trademark images
            transform: Optional torchvision transforms
            image_size: Target image size (height, width)
        """
        self.image_dir = image_dir
        self.image_size = image_size
        self.image_paths = self._load_image_paths()
        
        # Default transforms if none provided
        if transform is None:
            self.transform = transforms.Compose([
                transforms.Resize(image_size),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],  # ImageNet normalization
                    std=[0.229, 0.224, 0.225]
                )
            ])
        else:
            self.transform = transform
    
    def _load_image_paths(self) -> List[str]:
        """Load all valid image paths from the directory."""
        valid_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        image_paths = []
        
        if not os.path.exists(self.image_dir):
            print(f"Warning: Directory {self.image_dir} does not exist.")
            return image_paths
        
        for root, _, files in os.walk(self.image_dir):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in valid_extensions:
                    image_paths.append(os.path.join(root, file))
        
        print(f"Loaded {len(image_paths)} images from {self.image_dir}")
        return sorted(image_paths)
    
    def __len__(self) -> int:
        return len(self.image_paths)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, str]:
        """
        Get an image and its path.
        
        Returns:
            Tuple of (image_tensor, image_path)
        """
        image_path = self.image_paths[idx]
        
        try:
            # Load and convert to RGB
            image = Image.open(image_path).convert('RGB')
            
            # Apply transforms
            if self.transform:
                image = self.transform(image)
            
            return image, image_path
            
        except Exception as e:
            print(f"Error loading image {image_path}: {e}")
            # Return a blank image on error
            blank = torch.zeros(3, *self.image_size)
            return blank, image_path
    
    def get_image_names(self) -> List[str]:
        """Get list of image filenames."""
        return [os.path.basename(p) for p in self.image_paths]


class SiameseDataset(Dataset):
    """
    Dataset for Siamese Network training.
    Creates pairs of similar and dissimilar trademark images.
    """
    
    def __init__(
        self,
        image_dir: str,
        pairs_per_image: int = 5,
        transform: Optional[transforms.Compose] = None,
        image_size: Tuple[int, int] = (224, 224)
    ):
        """
        Initialize Siamese dataset.
        
        Args:
            image_dir: Directory containing trademark images
            pairs_per_image: Number of pairs to generate per image
            transform: Optional torchvision transforms
            image_size: Target image size
        """
        self.image_dir = image_dir
        self.pairs_per_image = pairs_per_image
        self.image_size = image_size
        
        # Load all image paths
        self.base_dataset = TrademarkDataset(image_dir, transform, image_size)
        self.image_paths = self.base_dataset.image_paths
        self.transform = self.base_dataset.transform
        
        # Generate pairs
        self.pairs = self._generate_pairs()
    
    def _generate_pairs(self) -> List[Tuple[int, int, int]]:
        """
        Generate pairs of images.
        Returns list of (idx1, idx2, label) where label=1 for similar, 0 for different.
        
        Note: Without labeled data, we create synthetic pairs:
        - Positive pairs: Same image with different augmentations
        - Negative pairs: Different images
        """
        pairs = []
        n_images = len(self.image_paths)
        
        if n_images < 2:
            return pairs
        
        for i in range(n_images):
            # Create positive pair (same image - will be augmented differently)
            pairs.append((i, i, 1))
            
            # Create negative pairs (different images)
            for _ in range(self.pairs_per_image - 1):
                j = random.randint(0, n_images - 1)
                while j == i:
                    j = random.randint(0, n_images - 1)
                pairs.append((i, j, 0))
        
        random.shuffle(pairs)
        return pairs
    
    def __len__(self) -> int:
        return len(self.pairs)
    
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get a pair of images and their similarity label.
        
        Returns:
            Tuple of (image1, image2, label)
        """
        idx1, idx2, label = self.pairs[idx]
        
        img1, _ = self.base_dataset[idx1]
        img2, _ = self.base_dataset[idx2]
        
        return img1, img2, torch.tensor(label, dtype=torch.float32)


def get_train_transforms(image_size: Tuple[int, int] = (224, 224)) -> transforms.Compose:
    """Get training transforms with data augmentation."""
    return transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(image_size),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(
            brightness=0.2,
            contrast=0.2,
            saturation=0.2,
            hue=0.1
        ),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def get_inference_transforms(image_size: Tuple[int, int] = (224, 224)) -> transforms.Compose:
    """Get inference transforms (no augmentation)."""
    return transforms.Compose([
        transforms.Resize(image_size),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])


def create_data_loaders(
    image_dir: str,
    batch_size: int = 32,
    num_workers: int = 4,
    train_split: float = 0.8,
    image_size: Tuple[int, int] = (224, 224)
) -> Tuple[DataLoader, DataLoader]:
    """
    Create train and validation data loaders.
    
    Args:
        image_dir: Directory containing images
        batch_size: Batch size for training
        num_workers: Number of worker processes
        train_split: Fraction of data for training
        image_size: Target image size
    
    Returns:
        Tuple of (train_loader, val_loader)
    """
    # Create full dataset
    full_dataset = TrademarkDataset(
        image_dir=image_dir,
        transform=get_train_transforms(image_size),
        image_size=image_size
    )
    
    # Split into train and validation
    n_total = len(full_dataset)
    n_train = int(n_total * train_split)
    n_val = n_total - n_train
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        full_dataset, [n_train, n_val]
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
        pin_memory=True
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True
    )
    
    return train_loader, val_loader


def load_single_image(
    image_path: str,
    image_size: Tuple[int, int] = (224, 224)
) -> torch.Tensor:
    """
    Load and preprocess a single image for inference.
    
    Args:
        image_path: Path to the image
        image_size: Target image size
    
    Returns:
        Preprocessed image tensor with batch dimension
    """
    transform = get_inference_transforms(image_size)
    
    image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image)
    
    # Add batch dimension
    return image_tensor.unsqueeze(0)


if __name__ == "__main__":
    # Example usage
    import sys
    
    # Test dataset loading
    dataset_path = os.path.join(os.path.dirname(__file__), "trademarks")
    
    if os.path.exists(dataset_path):
        dataset = TrademarkDataset(dataset_path)
        print(f"Dataset size: {len(dataset)}")
        
        if len(dataset) > 0:
            img, path = dataset[0]
            print(f"Image shape: {img.shape}")
            print(f"Image path: {path}")
    else:
        print(f"Dataset path {dataset_path} does not exist.")
        print("Please add trademark images to the dataset/trademarks folder.")
