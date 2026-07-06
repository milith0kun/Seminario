# Seminario Thesis Agent Guide

## Project Context

This repository contains a LaTeX thesis project about an SLM + RAG assistant for Quechua Collao. Treat the thesis text, bibliography, PDFs, notes, and generated research reports as academic material.

Use this workspace split:

- `Plan de Tesis/`: current LaTeX thesis, PDFs, bibliography, and chapter sources.
- `tesis-slm-quechua/`: technical project scaffold for data, RAG, inference, evaluation, models, experiments, dependencies, and implementation code.

## Working Rules

- Preserve the user's thesis content and existing uncommitted changes unless the user explicitly asks for edits.
- Before changing LaTeX, BibTeX, Markdown, DOCX, XLSX, PPTX, or PDF-derived content, inspect the relevant source files first.
- Prefer editing canonical sources such as `.tex`, `.bib`, `.md`, `.docx`, `.xlsx`, or `.pptx` instead of generated PDFs.
- Keep academic tone precise, technical, and non-commercial.
- Do not invent citations, DOIs, authors, years, metrics, datasets, or experimental results.
- When adding or revising sources, verify bibliographic data against reliable sources and keep BibTeX entries consistent.
- For LaTeX builds, use `latexmk -pdf` from the directory containing the main `.tex` file when available.
- Keep generated or temporary build files out of thesis prose changes unless the user asks for cleanup.

## Available Project Skills

The installed thesis/document skills are available in:

- `.claude/skills/` for Claude Code.
- `.agents/skills/` for Codex and other agents that scan project skills.
- `.agent/skills/` for Antigravity versions or setups that use the legacy singular path.

Use these skills when relevant:

- `academic-search`: academic paper discovery and research queries.
- `deep-research`: literature review and multi-source synthesis.
- `chat-with-pdf`: paper or thesis PDF Q&A.
- `pdf-extraction`: extract text, tables, and sections from PDFs.
- `content-research-writer`: academic drafting and revision.
- `doc-parser`: long-document structure extraction.
- `doc-pipeline`: document processing workflows.
- `docx-manipulation`: Word thesis document edits.
- `office-to-md`: convert Office files to Markdown.
- `md-to-office`: convert Markdown to Office documents.
- `diagram-creator`: architecture and workflow diagrams.
- `ai-slides`: thesis presentation decks.
- `qmd`: local notes and knowledge-base querying.
- `analyze-project`: inspect ML repositories and map training, inference, data, config, checkpoint, and risk surfaces.
- `ai-research-reproduction`: reproduce papers or model repositories with evidence and comparable results.
- `env-and-assets-bootstrap`: prepare local environments, datasets, caches, weights, and assets.
- `minimal-run-and-audit`: run minimal inference/evaluation checks and record latency, memory, and errors.
- `run-train`: run bounded training or QLoRA fine-tuning with logs, metrics, checkpoints, and adapters.
- `safe-debug`: diagnose CUDA, PyTorch, Transformers, dataset, and memory errors before changing code.
- `ai-research-explore`: explore controlled experimental variants without mixing candidates with verified results.
- `paper-context-resolver`: extract reproduction-critical details from papers.
- `find-skills`: discover additional task-specific skills.

## Technical Thesis Scope

- Target baseline: `Qwen2.5-3B-Instruct` with local RAG and optional QLoRA adapters.
- Put implementation code, datasets, models, experiment outputs, and notebooks under `tesis-slm-quechua/`.
- Avoid training from scratch.
- Keep RAG chunks short and traceable to sources.
- Keep Quechua Collao data labeled; do not mix Chanka, Cusco-Collao, and Collao variants without explicit tagging.
- For this Windows machine with GTX 1050 Ti 4 GB VRAM, treat 3B QLoRA as memory-constrained. Prefer inference, RAG, evaluation, and very small adapter dry runs first; use WSL2 Ubuntu for `bitsandbytes`.

## Agent Compatibility

`AGENTS.md` is the canonical instruction file for this workspace. Other editor-specific files in this repository should stay as thin pointers back to this file.
