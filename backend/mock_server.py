from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time

app = FastAPI()

# Allow browser requests from the frontend dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/upload")
async def upload_compat(file: UploadFile = File(...), top_k: int = Form(5)):
    start = time.time()
    # Return a deterministic mock response
    response = {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "processing_time_seconds": round(time.time() - start, 2),
        "uploaded_image": {"image_name": file.filename},
        "similar_trademarks": [
            {
                "rank": i+1,
                "brand_name": f"MockBrand{i+1}",
                "image_name": f"mock_image_{i+1}.jpg",
                "similarity_score": round(0.9 - i*0.05, 4),
                "similarity_percentage": int((0.9 - i*0.05)*100),
                "distance": round(0.1 + i*0.01, 6),
            }
            for i in range(top_k)
        ],
        "collision_risk": {
            "risk_level": "LOW",
            "message": "Mock response - no real analysis performed",
            "similarity_score": 0.9,
        },
        "detected": True,
        "top_score": 0.9,
        "dataset": {"num_images": 1000, "num_brands": 200, "num_categories": 10},
    }
    # Include CORS headers explicitly for browser clients
    return JSONResponse(content=response, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    })

@app.get("/api/v1/health")
async def health():
    return JSONResponse(content={"status": "healthy", "message": "Mock backend running"}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Credentials": "true",
    })


@app.options("/api/v1/upload")
async def upload_options():
    # Respond to CORS preflight explicitly
    return Response(status_code=200, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
        "Access-Control-Allow-Credentials": "true",
    })
