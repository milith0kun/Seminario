import os
import sys
from huggingface_hub import hf_hub_download, snapshot_download

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GGUF_DIR = os.path.join(BASE_DIR, "modelos", "gguf")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "modelos", "embeddings", "multilingual-e5-small")

os.makedirs(GGUF_DIR, exist_ok=True)
os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

print("=" * 60)
print("1. Descargando modelo de embeddings: intfloat/multilingual-e5-small")
print(f"Destino: {EMBEDDINGS_DIR}")
print("=" * 60)

snapshot_download(
    repo_id="intfloat/multilingual-e5-small",
    local_dir=EMBEDDINGS_DIR,
    local_dir_use_symlinks=False
)

print("\n" + "=" * 60)
print("2. Descargando SLM base cuantizado: Qwen/Qwen2.5-3B-Instruct-GGUF (qwen2.5-3b-instruct-q4_k_m.gguf)")
print(f"Destino: {GGUF_DIR}")
print("=" * 60)

hf_hub_download(
    repo_id="Qwen/Qwen2.5-3B-Instruct-GGUF",
    filename="qwen2.5-3b-instruct-q4_k_m.gguf",
    local_dir=GGUF_DIR,
    local_dir_use_symlinks=False
)

print("\n" + "=" * 60)
print("¡Descarga de modelos completada con éxito!")
print("=" * 60)
