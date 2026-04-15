# AI Trademark Collision Detection System

🛡️ An intelligent deep learning system that detects visual similarities between trademark logos to identify potential trademark collisions.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-orange.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)
![React](https://img.shields.io/badge/React-18.2+-61DAFB.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Overview

This system allows users to:
1. Upload a trademark/logo image
2. Compare it against a database of existing trademarks
3. Detect similar logos using deep learning (CNN/ResNet)
4. Get similarity scores and collision risk assessment
5. View results in an intuitive web interface

## 🏗️ Architecture

```
Frontend (React)
      ↓
Backend API (FastAPI)
      ↓
Feature Extraction Model (ResNet50)
      ↓
Vector Database / Similarity Search (FAISS)
      ↓
Trademark Dataset
```

## 📁 Project Structure

```
multimodal-trademark-collision-detection/
├── dataset/
│   ├── dataset_loader.py      # Dataset loading and preprocessing
│   └── trademarks/            # Trademark images directory
├── models/
│   ├── feature_extractor.py   # CNN feature extraction (ResNet50)
│   ├── generate_embeddings.py # Generate and save embeddings
│   ├── train_model.py         # Siamese Network training (optional)
│   └── embeddings.pkl         # Saved embeddings (generated)
├── similarity/
│   ├── faiss_index.py         # FAISS index management
│   └── search.py              # Similarity search engine
├── backend/
│   ├── main.py                # FastAPI application entry
│   ├── routes.py              # API endpoints
│   └── utils.py               # Utility functions
├── frontend/
│   ├── src/
│   │   ├── App.js             # Main React component
│   │   ├── components/        # UI components
│   │   └── index.css          # Styles
│   └── package.json           # Frontend dependencies
├── uploads/                    # Uploaded images directory
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- CUDA-capable GPU (optional, for faster processing)

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/multimodal-trademark-collision-detection.git
cd multimodal-trademark-collision-detection
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Add Trademark Images

Place your trademark images in the `dataset/trademarks/` directory.

```bash
# Example structure:
dataset/
└── trademarks/
    ├── brand1_logo.png
    ├── brand2_logo.jpg
    ├── company_trademark.png
    └── ...
```

### 4. Generate Embeddings

```bash
cd models
python generate_embeddings.py
```

This will:
- Load all trademark images from `dataset/trademarks/`
- Extract features using ResNet50
- Save embeddings to `embeddings.pkl`

### 5. Build FAISS Index

```bash
cd similarity
python faiss_index.py
```

This creates the FAISS index for fast similarity search.

### 6. Start the Backend API

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### 7. Start the Frontend

```bash
cd frontend
npm install
npm start
```

The frontend will be available at `http://localhost:3000`

## 🔌 API Endpoints

### POST `/api/v1/upload`

Upload a trademark image and find similar trademarks.

**Request:**
- `file`: Image file (multipart/form-data)
- `top_k`: Number of results to return (default: 5)

**Response:**
```json
{
  "status": "success",
  "uploaded_image": {
    "filename": "uploaded_logo.png",
    "url": "http://localhost:8000/uploads/..."
  },
  "similar_trademarks": [
    {
      "rank": 1,
      "image_name": "similar_brand.png",
      "image_url": "...",
      "similarity_score": 0.92,
      "similarity_percentage": 92.0
    }
  ],
  "collision_risk": {
    "risk_level": "HIGH",
    "message": "High collision risk detected",
    "similarity_score": 0.92
  }
}
```

### GET `/api/v1/stats`

Get system statistics.

### GET `/health`

Health check endpoint.

## 🧠 Model Details

### Feature Extraction

The system uses **ResNet50** pretrained on ImageNet to extract 2048-dimensional feature vectors from trademark images. The final classification layer is removed to use the model as a feature extractor.

Supported models:
- ResNet50 (default, 2048-dim)
- ResNet101 (2048-dim)
- EfficientNet-B0 (1280-dim)
- EfficientNet-B4 (1792-dim)
- VGG16 (4096-dim)

### Similarity Search

**FAISS** (Facebook AI Similarity Search) is used for efficient nearest neighbor search:
- Supports both L2 (Euclidean) and cosine similarity
- GPU acceleration available
- Scales to millions of vectors

### Collision Risk Levels

| Score | Risk Level | Description |
|-------|------------|-------------|
| ≥85%  | HIGH       | Very similar - likely trademark collision |
| 70-84%| MEDIUM     | Moderately similar - review recommended |
| <70%  | LOW        | Distinct - low collision risk |

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Model Configuration
MODEL_NAME=resnet50
EMBEDDING_DIM=2048

# FAISS Configuration
INDEX_TYPE=cosine
USE_GPU=false
```

### Frontend Configuration

Update `frontend/.env`:

```env
REACT_APP_API_URL=http://localhost:8000
```

## 📊 Optional: Training Siamese Network

For improved similarity detection, you can train a Siamese Network:

```bash
cd models
python train_model.py --dataset_path ../dataset/trademarks --epochs 50
```

## 🐳 Docker Deployment

### Build and Run

```bash
# Build backend
docker build -t trademark-api ./backend

# Run backend
docker run -p 8000:8000 trademark-api
```

### Docker Compose

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/app/uploads
      - ./models/embeddings.pkl:/app/models/embeddings.pkl
      
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## 📈 Evaluation Metrics

The system can be evaluated using:
- **Precision@K**: Fraction of relevant results in top K
- **Recall@K**: Fraction of relevant items retrieved
- **Mean Average Precision (mAP)**
- **Cosine Similarity Distribution**

## 🔮 Future Enhancements

- [ ] Grad-CAM heatmap visualization
- [ ] Multi-modal search (image + text)
- [ ] Trademark text extraction (OCR)
- [ ] Historical collision tracking
- [ ] Batch processing support
- [ ] User authentication
- [ ] API rate limiting

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📧 Contact

For questions or support, please open an issue on GitHub.