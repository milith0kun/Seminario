# Thesis Project Initialization

## Goal

Initialize this repository as an offline Spanish-Quechua Collao educational assistant project using a compact instruct model, disciplined local RAG, linguistic resources, and optional QLoRA adapters.

## Baseline Stack

- Base model: `Qwen2.5-3B-Instruct`.
- Inference: Ollama for quick tests, llama.cpp/GGUF for offline delivery.
- RAG: FAISS or ChromaDB, BM25, multilingual embeddings.
- Fine-tuning: PEFT + TRL, QLoRA rank 8 or 16 only if hardware allows.
- Evaluation: chrF++, SacreBLEU, RAGAS, Recall@k, MRR, nDCG, latency, RAM, tokens/s, and human EIB rubric.

## First Agent Prompt

Use this as the first project command in Claude Code, Codex, or Antigravity:

```text
/analyze-project
Este será mi proyecto de tesis: asistente educativo offline español-Quechua Collao con Qwen2.5-3B, RAG local, glosarios y QLoRA opcional. Diseña el mapa técnico del repositorio, archivos principales, pipeline de datos, entrenamiento, evaluación e inferencia local. No entrenes desde cero. No inventes citas, datasets ni métricas. Prioriza reproducibilidad, logs, comparabilidad y ejecución local.
```

## Experiment Phases

1. `E1_base`: model-only baseline with fixed question set.
2. `E2_rag`: local RAG with vector + BM25 retrieval.
3. `E3_rules`: prompt/rules baseline without RAG.
4. `E4_rag_rules`: RAG plus disciplined prompts and terminology rules.
5. `E5_qlora`: small QLoRA adapter, if feasible.
6. `E6_hybrid`: RAG plus QLoRA plus rules.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-core.txt
```

For QLoRA on this Windows machine, prefer WSL2 Ubuntu before installing:

```bash
pip install -r requirements-qlora-wsl.txt
```

## Hardware Note

This machine has an NVIDIA GTX 1050 Ti with 4 GB VRAM. Treat QLoRA on 3B models as experimental and memory-constrained. Start with inference, RAG, evaluation, and tiny adapter dry runs before any long training.
