import os
from huggingface_hub import hf_hub_download

ROOT_DIR = r"D:\Proyectos\Seminario"
ROOT_GGUF_DIR = os.path.join(ROOT_DIR, "modelos", "gguf")
os.makedirs(ROOT_GGUF_DIR, exist_ok=True)

# Lista completa de modelos candidatos de la Tabla 2 del Marco Teórico
modelos_candidatos = [
    {
        "nombre": "Qwen2.5-7B-Instruct (Variante 16GB RAM)",
        "repo_id": "bartowski/Qwen2.5-7B-Instruct-GGUF",
        "archivo": "Qwen2.5-7B-Instruct-Q4_K_M.gguf"
    },
    {
        "nombre": "Llama-3.2-3B-Instruct (Alternativa Meta)",
        "repo_id": "bartowski/Llama-3.2-3B-Instruct-GGUF",
        "archivo": "Llama-3.2-3B-Instruct-Q4_K_M.gguf"
    },
    {
        "nombre": "Gemma-2-2B-IT (Alternativa Google)",
        "repo_id": "bartowski/gemma-2-2b-it-GGUF",
        "archivo": "gemma-2-2b-it-Q4_K_M.gguf"
    },
    {
        "nombre": "SmolLM2-1.7B-Instruct (Hardware ultra-restringido)",
        "repo_id": "HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF",
        "archivo": "smollm2-1.7b-instruct-q4_k_m.gguf"
    }
]

for idx, m in enumerate(modelos_candidatos, 1):
    print("=" * 65)
    print(f"[{idx}/{len(modelos_candidatos)}] Descargando: {m['nombre']}")
    print(f"Repositorio: {m['repo_id']}")
    print(f"Archivo: {m['archivo']}")
    print("=" * 65)
    
    path_descarga = hf_hub_download(
        repo_id=m["repo_id"],
        filename=m["archivo"],
        local_dir=ROOT_GGUF_DIR
    )
    print(f"Descargado con éxito en: {path_descarga}\n")

print("=" * 65)
print("¡Todos los modelos candidatos del Plan de Tesis están descargados!")
print("=" * 65)
