"""
Grad-CAM Visualization for Trademark Similarity
Generates heatmaps showing which regions of logos are most similar
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import models, transforms
from PIL import Image
import numpy as np
import cv2
import os
from typing import Tuple, Optional

from dataset.dataset_loader import get_default_dataset_root


class GradCAM:
    """
    Grad-CAM implementation for CNN visualization
    Highlights important regions in trademark images
    """
    
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        """
        Initialize Grad-CAM
        
        Args:
            model: CNN model (e.g., ResNet50)
            target_layer: Layer to compute Grad-CAM for
        """
        self.model = model
        self.target_layer = target_layer
        self.gradients = None
        self.activations = None
        
        # Register hooks
        self._register_hooks()
    
    def _register_hooks(self):
        """Register forward and backward hooks"""
        def forward_hook(module, input, output):
            self.activations = output.detach()
        
        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()
        
        self.target_layer.register_forward_hook(forward_hook)
        self.target_layer.register_full_backward_hook(backward_hook)
    
    def generate_cam(
        self, 
        input_tensor: torch.Tensor, 
        target_class: Optional[int] = None
    ) -> np.ndarray:
        """
        Generate Grad-CAM heatmap
        
        Args:
            input_tensor: Input image tensor (1, C, H, W)
            target_class: Target class index (default: predicted class)
            
        Returns:
            Grad-CAM heatmap as numpy array
        """
        self.model.eval()
        
        # Forward pass
        output = self.model(input_tensor)
        
        if target_class is None:
            target_class = output.argmax(dim=1).item()
        
        # Backward pass
        self.model.zero_grad()
        output[0, target_class].backward()
        
        # Compute weights
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        
        # Compute Grad-CAM
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        
        # Normalize
        cam = cam.squeeze().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        
        return cam


class SimilarityGradCAM:
    """
    Grad-CAM for trademark similarity visualization
    Shows which parts of two logos are most similar
    """
    
    def __init__(self, model_name: str = 'resnet50', device: str = None):
        """
        Initialize Similarity Grad-CAM
        
        Args:
            model_name: Name of the pretrained model
            device: Device to use ('cuda' or 'cpu')
        """
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load model
        if model_name == 'resnet50':
            self.model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
            self.target_layer = self.model.layer4[-1]
        elif model_name == 'resnet101':
            self.model = models.resnet101(weights=models.ResNet101_Weights.IMAGENET1K_V2)
            self.target_layer = self.model.layer4[-1]
        else:
            raise ValueError(f"Unsupported model: {model_name}")
        
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Image transforms
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        # Initialize Grad-CAM
        self.gradcam = GradCAM(self.model, self.target_layer)
    
    def preprocess_image(self, image_path: str) -> Tuple[torch.Tensor, np.ndarray]:
        """
        Preprocess image for Grad-CAM
        
        Args:
            image_path: Path to image file
            
        Returns:
            Tuple of (tensor, original_image)
        """
        image = Image.open(image_path).convert('RGB')
        original = np.array(image.resize((224, 224)))
        
        tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        return tensor, original
    
    def generate_heatmap(
        self, 
        image_path: str,
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for a single image
        
        Args:
            image_path: Path to image file
            save_path: Optional path to save visualization
            
        Returns:
            Heatmap overlaid on original image
        """
        tensor, original = self.preprocess_image(image_path)
        
        # Generate CAM
        cam = self.gradcam.generate_cam(tensor)
        
        # Resize CAM to image size
        cam_resized = cv2.resize(cam, (224, 224))
        
        # Create heatmap
        heatmap = cv2.applyColorMap(
            np.uint8(255 * cam_resized), 
            cv2.COLORMAP_JET
        )
        heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        
        # Overlay on original image
        overlay = np.float32(heatmap) * 0.4 + np.float32(original) * 0.6
        overlay = np.uint8(np.clip(overlay, 0, 255))
        
        if save_path:
            Image.fromarray(overlay).save(save_path)
        
        return overlay
    
    def compare_trademarks(
        self,
        image1_path: str,
        image2_path: str,
        save_path: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate side-by-side comparison with heatmaps
        
        Args:
            image1_path: Path to first trademark image
            image2_path: Path to second trademark image
            save_path: Optional path to save comparison
            
        Returns:
            Side-by-side visualization
        """
        # Generate heatmaps
        heatmap1 = self.generate_heatmap(image1_path)
        heatmap2 = self.generate_heatmap(image2_path)
        
        # Load original images
        orig1 = np.array(Image.open(image1_path).convert('RGB').resize((224, 224)))
        orig2 = np.array(Image.open(image2_path).convert('RGB').resize((224, 224)))
        
        # Create comparison grid
        # Row 1: Original images
        # Row 2: Heatmaps
        top_row = np.hstack([orig1, orig2])
        bottom_row = np.hstack([heatmap1, heatmap2])
        comparison = np.vstack([top_row, bottom_row])
        
        if save_path:
            Image.fromarray(comparison).save(save_path)
        
        return comparison
    
    def generate_similarity_heatmap(
        self,
        query_path: str,
        match_path: str,
        save_path: Optional[str] = None
    ) -> dict:
        """
        Generate detailed similarity visualization between two logos
        
        Args:
            query_path: Path to query trademark
            match_path: Path to matched trademark
            save_path: Optional path to save visualization
            
        Returns:
            Dictionary with visualization data
        """
        # Generate individual heatmaps
        query_heatmap = self.generate_heatmap(query_path)
        match_heatmap = self.generate_heatmap(match_path)
        
        # Load originals
        query_orig = np.array(Image.open(query_path).convert('RGB').resize((224, 224)))
        match_orig = np.array(Image.open(match_path).convert('RGB').resize((224, 224)))
        
        # Create comprehensive visualization
        padding = np.ones((224, 10, 3), dtype=np.uint8) * 255
        
        row1 = np.hstack([query_orig, padding, match_orig])
        row2 = np.hstack([query_heatmap, padding, match_heatmap])
        
        final = np.vstack([row1, row2])
        
        if save_path:
            Image.fromarray(final).save(save_path)
        
        return {
            'query_heatmap': query_heatmap,
            'match_heatmap': match_heatmap,
            'comparison': final
        }


def create_risk_visualization(
    similarity_score: float,
    image: np.ndarray,
    save_path: Optional[str] = None
) -> np.ndarray:
    """
    Add risk level indicator to image
    
    Args:
        similarity_score: Similarity score (0-1)
        image: Image to annotate
        save_path: Optional path to save
        
    Returns:
        Annotated image
    """
    # Determine risk color
    if similarity_score >= 0.85:
        color = (255, 0, 0)  # Red
        text = "HIGH RISK"
    elif similarity_score >= 0.70:
        color = (255, 165, 0)  # Orange
        text = "MEDIUM RISK"
    else:
        color = (0, 255, 0)  # Green
        text = "LOW RISK"
    
    # Add border
    annotated = cv2.copyMakeBorder(
        image, 5, 30, 5, 5,
        cv2.BORDER_CONSTANT,
        value=color
    )
    
    # Add text
    cv2.putText(
        annotated,
        f"{text}: {similarity_score*100:.1f}%",
        (10, annotated.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )
    
    if save_path:
        cv2.imwrite(save_path, cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR))
    
    return annotated


if __name__ == "__main__":
    print("Grad-CAM Visualization Demo")
    print("=" * 60)
    
    # Initialize
    visualizer = SimilarityGradCAM(model_name='resnet50')
    
    # Test with sample images if available
    sample_dir = str(get_default_dataset_root())
    
    if os.path.exists(sample_dir):
        images = [f for f in os.listdir(sample_dir) 
                  if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        if len(images) >= 2:
            img1 = os.path.join(sample_dir, images[0])
            img2 = os.path.join(sample_dir, images[1])
            
            print(f"\nGenerating comparison for:")
            print(f"  Image 1: {images[0]}")
            print(f"  Image 2: {images[1]}")
            
            comparison = visualizer.compare_trademarks(
                img1, img2,
                save_path="comparison_heatmap.png"
            )
            
            print(f"\nSaved comparison to: comparison_heatmap.png")
        else:
            print("Not enough images in dataset for comparison")
    else:
        print(f"Dataset directory not found: {sample_dir}")
