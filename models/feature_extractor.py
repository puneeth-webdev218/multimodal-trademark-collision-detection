"""Image feature extraction for trademark logos.

Preferred backend: CLIP (ViT-B/32) using local pretrained artifacts.
Fallback backend: deterministic local descriptor for offline reliability.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Sequence, Union

import numpy as np
from PIL import Image, ImageOps

LOGGER = logging.getLogger(__name__)

ImageLike = Union[str, Path, Image.Image]


class FeatureExtractor:
    def __init__(
        self,
        model_name: str = "auto",
        clip_model_id: str = "openai/clip-vit-base-patch32",
        device: Optional[str] = None,
        image_size: int = 224,
    ) -> None:
        self.device = device or self._auto_device()
        self.model_name = model_name.lower()
        self.clip_model_id = clip_model_id
        self.image_size = image_size

        self.backend = ""
        self.embedding_dim = 0

        self.clip_model = None
        self.clip_processor = None
        self.resnet_model = None

        self._load_model()

    @staticmethod
    def _auto_device() -> str:
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def _load_model(self) -> None:
        if self.model_name in {"clip", "auto"}:
            self._try_load_clip()

        if self.backend:
            return

        self.backend = "simple"
        self.embedding_dim = 3384
        LOGGER.info("Using simple local image descriptor backend on device=%s", self.device)

    def _try_load_clip(self) -> None:
        try:
            import torch
            from transformers import CLIPModel, CLIPProcessor  # type: ignore[import-not-found]
        except Exception:
            return

        try:
            self.clip_processor = CLIPProcessor.from_pretrained(self.clip_model_id, local_files_only=True)
            self.clip_model = CLIPModel.from_pretrained(self.clip_model_id, local_files_only=True).to(self.device)
            self.clip_model.eval()
            self.backend = "clip"
            self.embedding_dim = int(self.clip_model.config.projection_dim)
            LOGGER.info("Using CLIP backend: %s on device=%s", self.clip_model_id, self.device)
        except Exception as exc:
            LOGGER.info("CLIP backend unavailable, falling back to local descriptor: %s", exc)
            self.clip_model = None
            self.clip_processor = None
            self.backend = ""

    @staticmethod
    def _normalize(embeddings: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / np.clip(norms, 1e-12, None)

    @staticmethod
    def _ensure_rgb(image: ImageLike) -> Image.Image:
        if isinstance(image, Image.Image):
            pil_image = image
        else:
            pil_image = Image.open(image)

        if pil_image.mode in {"RGBA", "LA", "P"}:
            background = Image.new("RGBA", pil_image.size, (255, 255, 255, 255))
            background.paste(pil_image.convert("RGBA"), mask=pil_image.convert("RGBA").split()[-1])
            pil_image = background.convert("RGB")
        else:
            pil_image = pil_image.convert("RGB")

        return ImageOps.fit(pil_image, (224, 224), method=Image.Resampling.LANCZOS)

    @staticmethod
    def _simple_descriptor(image: Image.Image) -> np.ndarray:
        rgb = np.asarray(image.convert("RGB"), dtype=np.float32) / 255.0

        # Preserve coarse layout information.
        downsampled = ImageOps.fit(image, (32, 32), method=Image.Resampling.LANCZOS)
        downsampled_arr = np.asarray(downsampled, dtype=np.float32) / 255.0
        downsampled_vec = downsampled_arr.reshape(-1)

        # Add color histograms to make the descriptor robust to simple logo variations.
        hist_parts: List[np.ndarray] = []
        for channel in range(3):
            hist, _ = np.histogram(rgb[:, :, channel], bins=16, range=(0.0, 1.0), density=True)
            hist_parts.append(hist.astype(np.float32))

        # Lightweight grayscale texture descriptor.
        grayscale = rgb.mean(axis=2)
        gx = np.abs(np.diff(grayscale, axis=1, append=grayscale[:, -1:]))
        gy = np.abs(np.diff(grayscale, axis=0, append=grayscale[-1:, :]))
        texture = np.stack([grayscale, gx, gy], axis=0)
        texture = Image.fromarray(np.clip(texture.mean(axis=0) * 255.0, 0, 255).astype(np.uint8))
        texture = ImageOps.fit(texture, (16, 16), method=Image.Resampling.LANCZOS)
        texture_vec = np.asarray(texture, dtype=np.float32).reshape(-1) / 255.0

        stats = np.array(
            [
                float(rgb.mean()),
                float(rgb.std()),
                float(grayscale.mean()),
                float(grayscale.std()),
                float((rgb[:, :, 0] > 0.95).mean()),
                float((rgb[:, :, 1] > 0.95).mean()),
                float((rgb[:, :, 2] > 0.95).mean()),
                float((rgb[:, :, :] < 0.05).mean()),
            ],
            dtype=np.float32,
        )

        vector = np.concatenate([downsampled_vec, *hist_parts, texture_vec, stats]).astype(np.float32)
        return vector

    def _extract_simple(self, image: ImageLike) -> np.ndarray:
        pil_img = self._ensure_rgb(image)
        vector = self._simple_descriptor(pil_img)
        vector = vector.reshape(1, -1)
        vector = self._normalize(vector)
        return vector[0]

    def _extract_clip(self, image: ImageLike) -> np.ndarray:
        assert self.clip_model is not None and self.clip_processor is not None
        import torch

        pil_img = self._ensure_rgb(image)
        inputs = self.clip_processor(images=pil_img, return_tensors="pt")
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.no_grad():
            output = self.clip_model.get_image_features(**inputs)
            # Output is already the image features tensor, not an object
            if isinstance(output, torch.Tensor):
                vector = output.detach().cpu().numpy().astype(np.float32)
            elif hasattr(output, 'pooler_output'):
                features = output.pooler_output
                vector = features.detach().cpu().numpy().astype(np.float32)
            else:
                # Fallback: treat as object with last_hidden_state
                features = output.last_hidden_state.mean(dim=1) if hasattr(output, 'last_hidden_state') else output
                vector = features.detach().cpu().numpy().astype(np.float32)
        vector = self._normalize(vector)
        return vector[0]

    def _extract_clip_batch(self, images: Sequence[ImageLike]) -> np.ndarray:
        assert self.clip_model is not None and self.clip_processor is not None
        import torch

        pil_images = [self._ensure_rgb(image) for image in images]
        inputs = self.clip_processor(images=pil_images, return_tensors="pt", padding=True)
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.no_grad():
            output = self.clip_model.get_image_features(**inputs)
            # Output is already the image features tensor, not an object
            if isinstance(output, torch.Tensor):
                vectors = output.detach().cpu().numpy().astype(np.float32)
            elif hasattr(output, 'pooler_output'):
                features = output.pooler_output
                vectors = features.detach().cpu().numpy().astype(np.float32)
            else:
                # Fallback: treat as object with last_hidden_state
                features = output.last_hidden_state.mean(dim=1) if hasattr(output, 'last_hidden_state') else output
                vectors = features.detach().cpu().numpy().astype(np.float32)
        return self._normalize(vectors)

    def extract_embedding(self, image: ImageLike) -> Optional[np.ndarray]:
        try:
            if self.backend == "clip":
                return self._extract_clip(image)
            return self._extract_simple(image)
        except Exception as exc:
            LOGGER.exception("Failed to extract embedding: %s", exc)
            return None

    def extract_features(self, image_path: str) -> Optional[np.ndarray]:
        return self.extract_embedding(image_path)

    def extract_batch_embeddings(self, image_paths: Sequence[str], batch_size: int = 32) -> np.ndarray:
        vectors, _ = self.extract_batch_embeddings_with_paths(image_paths=image_paths, batch_size=batch_size)
        return vectors

    def extract_batch_embeddings_with_paths(
        self,
        image_paths: Sequence[str],
        batch_size: int = 32,
    ) -> tuple[np.ndarray, List[str]]:
        vectors: List[np.ndarray] = []
        kept_paths: List[str] = []

        for start in range(0, len(image_paths), batch_size):
            chunk = image_paths[start : start + batch_size]
            if self.backend == "clip":
                batch_images: List[Image.Image] = []
                batch_paths: List[str] = []
                for path in chunk:
                    try:
                        batch_images.append(self._ensure_rgb(path))
                        batch_paths.append(path)
                    except Exception:
                        continue
                if not batch_images:
                    continue
                try:
                    batch_vectors = self._extract_clip_batch(batch_images)
                    vectors.extend([row.astype(np.float32) for row in batch_vectors])
                    kept_paths.extend(batch_paths)
                except Exception:
                    # Fallback to per-image extraction if a whole batch fails.
                    for path in batch_paths:
                        vector = self.extract_embedding(path)
                        if vector is not None:
                            vectors.append(vector.astype(np.float32))
                            kept_paths.append(path)
            else:
                for path in chunk:
                    try:
                        vector = self.extract_embedding(path)
                        if vector is None:
                            continue
                        vectors.append(vector.astype(np.float32))
                        kept_paths.append(path)
                    except Exception:
                        continue

        if not vectors:
            return np.empty((0, self.embedding_dim), dtype=np.float32), []

        return np.asarray(vectors, dtype=np.float32), kept_paths


def load_model(model_name: str = "auto", device: Optional[str] = None) -> FeatureExtractor:
    return FeatureExtractor(model_name=model_name, device=device)


def extract_embedding(image: ImageLike, model: Optional[FeatureExtractor] = None) -> Optional[np.ndarray]:
    extractor = model if model else load_model()
    return extractor.extract_embedding(image)


def extract_features(image: ImageLike, model: Optional[FeatureExtractor] = None) -> Optional[np.ndarray]:
    return extract_embedding(image=image, model=model)
