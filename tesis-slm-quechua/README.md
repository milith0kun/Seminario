# Seminario: SLM + RAG Quechua Collao

Proyecto de tesis para un asistente educativo offline español-Quechua Collao con modelo compacto, RAG local, recursos linguisticos y adaptacion QLoRA opcional.

## Agent Setup

Project instructions are in `AGENTS.md`.

Skills are available in:

- `.agents/skills/` for Codex, Antigravity and compatible agents.
- `.agent/skills/` for Antigravity legacy workspace discovery.
- `.claude/skills/` for Claude Code.

Start with `PROJECT_INIT.md`.

## Technical Layout

- `data/`: raw, cleaned, RAG, training, eval and synthetic datasets.
- `models/`: base models, GGUF exports and LoRA adapters.
- `src/`: ingest, RAG, fine-tuning, inference, evaluation and app code.
- `experiments/`: controlled experiment runs E1 to E6.
- `reports/`: generated experiment reports.
- `Plan de Tesis/`: current thesis sources and documents.
