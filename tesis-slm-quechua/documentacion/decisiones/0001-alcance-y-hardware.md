# Decision 0001: Alcance Y Hardware

El prototipo sera textual y offline.

Hardware observado:
- GPU: NVIDIA GTX 1050 Ti, 4 GB VRAM.
- Sistema local: Windows.
- Python: 3.11 en `tesis-slm-quechua/.venv`.

Implicancias:
- Qwen2.5-3B-Instruct es el modelo local por defecto.
- Inferencia offline prioritaria via GGUF Q4_K_M + llama.cpp.
- 7B queda como variante de calidad solo si hay RAM suficiente.
- QLoRA es opcional y debe ejecutarse en WSL2, Colab o Kaggle.
- RAG y evaluacion deben funcionar antes de iniciar QLoRA.
- n_gpu_layers inicia en 0 (CPU) para estabilidad; se puede subir si hay VRAM libre.
