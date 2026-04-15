"""
Training script for Siamese Network (Optional Enhancement)
Trains a model to better distinguish between similar and different trademarks
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import os
import random
import numpy as np


class SiameseNetwork(nn.Module):
    """
    Siamese Network for learning trademark similarity
    Uses shared weights for both input images
    """
    
    def __init__(self, embedding_dim=512):
        super(SiameseNetwork, self).__init__()
        
        # Load pretrained ResNet50 as backbone (modern API)
        resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        
        # Remove final FC layer
        self.backbone = nn.Sequential(*list(resnet.children())[:-1])
        
        # Add custom embedding layer
        self.embedding = nn.Sequential(
            nn.Linear(2048, 1024),
            nn.ReLU(inplace=True),
            nn.Dropout(0.2),
            nn.Linear(1024, embedding_dim),
        )
        
    def forward_once(self, x):
        """Forward pass for one image"""
        output = self.backbone(x)
        output = output.view(output.size()[0], -1)
        output = self.embedding(output)
        return output
    
    def forward(self, input1, input2):
        """Forward pass for image pair"""
        output1 = self.forward_once(input1)
        output2 = self.forward_once(input2)
        return output1, output2


class ContrastiveLoss(nn.Module):
    """
    Contrastive Loss function
    Pulls similar pairs together and pushes dissimilar pairs apart
    """
    
    def __init__(self, margin=2.0):
        super(ContrastiveLoss, self).__init__()
        self.margin = margin
    
    def forward(self, output1, output2, label):
        """
        Args:
            output1: Embedding of first image
            output2: Embedding of second image
            label: 1 if similar, 0 if dissimilar
        """
        euclidean_distance = nn.functional.pairwise_distance(output1, output2)
        
        loss_contrastive = torch.mean(
            (label) * torch.pow(euclidean_distance, 2) +
            (1 - label) * torch.pow(torch.clamp(self.margin - euclidean_distance, min=0.0), 2)
        )
        
        return loss_contrastive


class TrademarkPairDataset(Dataset):
    """
    Dataset class for trademark pairs
    Generates positive (similar) and negative (dissimilar) pairs
    """
    
    def __init__(self, root_dir, transform=None):
        """
        Args:
            root_dir: Root directory containing trademark images
            transform: Image transformations
        """
        self.root_dir = root_dir
        self.transform = transform
        self.image_paths = []
        self.labels = []
        
        # Load all images and organize by class/category
        self.classes = {}
        for class_name in os.listdir(root_dir):
            class_path = os.path.join(root_dir, class_name)
            if os.path.isdir(class_path):
                images = [os.path.join(class_path, img) for img in os.listdir(class_path)
                         if img.lower().endswith(('.png', '.jpg', '.jpeg'))]
                if images:
                    self.classes[class_name] = images
        
        # If no class structure, treat all images as separate classes
        if not self.classes:
            self.classes = {}
            for img in os.listdir(root_dir):
                if img.lower().endswith(('.png', '.jpg', '.jpeg')):
                    img_path = os.path.join(root_dir, img)
                    self.classes[img] = [img_path]
        
        self.class_names = list(self.classes.keys())
        
    def __len__(self):
        return len(self.class_names) * 100  # Generate 100 pairs per class
    
    def __getitem__(self, idx):
        """
        Returns a pair of images and their similarity label
        """
        # Randomly decide to create a positive or negative pair
        should_get_same_class = random.random() > 0.5
        
        if should_get_same_class and len(self.classes) > 0:
            # Positive pair - same class
            class_name = random.choice(self.class_names)
            if len(self.classes[class_name]) >= 2:
                img1_path, img2_path = random.sample(self.classes[class_name], 2)
            else:
                img1_path = img2_path = random.choice(self.classes[class_name])
            label = 1.0
        else:
            # Negative pair - different classes
            if len(self.class_names) >= 2:
                class1, class2 = random.sample(self.class_names, 2)
                img1_path = random.choice(self.classes[class1])
                img2_path = random.choice(self.classes[class2])
            else:
                class_name = random.choice(self.class_names)
                img1_path = img2_path = random.choice(self.classes[class_name])
            label = 0.0
        
        # Load images
        img1 = Image.open(img1_path).convert('RGB')
        img2 = Image.open(img2_path).convert('RGB')
        
        # Apply transformations
        if self.transform:
            img1 = self.transform(img1)
            img2 = self.transform(img2)
        
        return img1, img2, torch.tensor([label], dtype=torch.float32)


def train_siamese_network(dataset_path, num_epochs=50, batch_size=32, learning_rate=0.0001):
    """
    Train the Siamese Network
    
    Args:
        dataset_path: Path to trademark dataset
        num_epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")
    
    # Data transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])
    
    # Create dataset and dataloader
    dataset = TrademarkPairDataset(dataset_path, transform=transform)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=2)
    
    # Initialize model, loss, and optimizer
    model = SiameseNetwork(embedding_dim=512).to(device)
    criterion = ContrastiveLoss(margin=2.0)
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    
    # Training loop
    print(f"Starting training for {num_epochs} epochs...")
    
    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        
        for i, (img1, img2, label) in enumerate(dataloader):
            img1, img2, label = img1.to(device), img2.to(device), label.to(device)
            
            # Forward pass
            optimizer.zero_grad()
            output1, output2 = model(img1, img2)
            loss = criterion(output1, output2, label)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            
            if (i + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{num_epochs}], Step [{i+1}/{len(dataloader)}], Loss: {loss.item():.4f}")
        
        avg_loss = running_loss / len(dataloader)
        print(f"Epoch [{epoch+1}/{num_epochs}] Average Loss: {avg_loss:.4f}")
        
        # Save checkpoint every 10 epochs
        if (epoch + 1) % 10 == 0:
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'loss': avg_loss,
            }, f'siamese_checkpoint_epoch_{epoch+1}.pth')
            print(f"Checkpoint saved at epoch {epoch+1}")
    
    # Save final model
    torch.save(model.state_dict(), 'siamese_model_final.pth')
    print("Training completed! Model saved.")
    
    return model


if __name__ == "__main__":
    # Example usage
    dataset_path = "../dataset/trademarks"
    
    if os.path.exists(dataset_path):
        model = train_siamese_network(
            dataset_path=dataset_path,
            num_epochs=50,
            batch_size=16,
            learning_rate=0.0001
        )
    else:
        print(f"Dataset path {dataset_path} does not exist.")
        print("Please add trademark images to the dataset/trademarks folder.")
