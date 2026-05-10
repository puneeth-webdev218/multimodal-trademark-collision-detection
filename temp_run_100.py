from pathlib import Path
import time

from models.generate_embeddings import load_or_generate_logo_embeddings
from similarity.faiss_index import build_index_from_embeddings
from similarity.search import SimilaritySearch

base = Path.cwd()
emb_path = base / "models" / "logo_embeddings.pkl"
idx_path = base / "similarity" / "faiss_index.index"
meta_path = base / "similarity" / "index_metadata.pkl"

print("Step 1: Generate embeddings from dataset/subset")
start = time.time()
payload = load_or_generate_logo_embeddings(
    dataset_root=str(base / "dataset" / "subset"),
    embeddings_path=str(emb_path),
    model_name="simple",
    force_recompute=True,
    batch_size=32,
)
print(f"Embeddings ready: {payload['indexed_num_images']} images in {time.time() - start:.1f}s")

print("Step 2: Build FAISS index")
start = time.time()
build_index_from_embeddings(str(emb_path), str(idx_path), str(meta_path))
print(f"FAISS ready in {time.time() - start:.1f}s")

print("Step 3: Validate search engine")
engine = SimilaritySearch(dataset_root=str(base / "dataset" / "subset"))
result = engine.run_self_match_test(sample_size=5)
print(f"Self-match validation: {result}")
print("DONE")
