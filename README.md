# Seminario: Asistente SLM + RAG para Quechua Collao

Repositorio de tesis y prototipo tecnico para un asistente educativo offline espanol-Quechua Collao. El trabajo combina un modelo compacto, recuperacion aumentada por documentos locales, recursos linguisticos y una adaptacion ligera opcional con QLoRA.

## Objetivo

Construir y evaluar un asistente local que pueda responder consultas educativas bilingues usando:

- un modelo base compacto, inicialmente `Qwen2.5-3B-Instruct`;
- RAG local con corpus curado, glosarios y documentos de apoyo;
- busqueda hibrida con embeddings y BM25;
- evaluacion reproducible de recuperacion, generacion, latencia y uso de memoria;
- fine-tuning QLoRA solo como experimento opcional, no como entrenamiento desde cero.

## Estructura Del Repositorio

```text
Plan de Tesis/
  Fuentes LaTeX, capitulos, bibliografia, PDFs y documentos academicos.

tesis-slm-quechua/
  Proyecto tecnico: datos, modelos, RAG, inferencia, evaluacion,
  experimentos, dependencias y scripts futuros.

.agents/skills/
.agent/skills/
.claude/skills/
  Skills instalados para Codex, Antigravity, Claude Code y agentes compatibles.

AGENTS.md
  Instrucciones canonicas para agentes que trabajen en este repositorio.
```

## Flujo De Trabajo

1. Redactar y mantener la tesis en `Plan de Tesis/`.
2. Desarrollar el prototipo tecnico en `tesis-slm-quechua/`.
3. Registrar experimentos en `tesis-slm-quechua/experiments/`.
4. Guardar reportes tecnicos en `tesis-slm-quechua/reports/`.
5. Llevar resultados validados de vuelta a la tesis, con citas y metricas verificables.

## Inicio Rapido

```powershell
cd D:\Proyectos\Seminario\tesis-slm-quechua
.\.venv\Scripts\Activate.ps1
python --version
```

Si se necesita reconstruir el entorno:

```powershell
python -m venv .venv --system-site-packages
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-core.txt
```

Para QLoRA con `bitsandbytes` o `unsloth`, usar preferentemente WSL2 Ubuntu:

```bash
pip install -r requirements-qlora-wsl.txt
```

## Experimentos Planeados

- `E1_base`: modelo base sin RAG.
- `E2_rag`: RAG local con recuperacion hibrida.
- `E3_rules`: reglas y prompts sin RAG.
- `E4_rag_rules`: RAG mas reglas terminologicas.
- `E5_qlora`: adaptador QLoRA pequeno, si el hardware lo permite.
- `E6_hybrid`: RAG + QLoRA + reglas.

## Stack Tecnico

- Modelos: Qwen2.5-3B-Instruct como base inicial.
- Inferencia local: Ollama para pruebas rapidas; llama.cpp/GGUF para entrega offline.
- RAG: FAISS o ChromaDB, BM25, sentence-transformers.
- Fine-tuning: PEFT, TRL, QLoRA opcional.
- Evaluacion: RAGAS, SacreBLEU, BERTScore, Recall@k, MRR, nDCG, latencia, RAM y tokens/s.

## Notas Importantes

- No entrenar desde cero.
- No inventar citas, datasets, metricas ni resultados.
- No mezclar variantes de Quechua sin etiquetado y validacion.
- Mantener los datos, modelos y salidas pesadas fuera de Git; solo se versionan placeholders y configuracion.
- La maquina local tiene una GTX 1050 Ti de 4 GB, por lo que QLoRA en 3B debe tratarse como experimento limitado.

## Para Agentes

Antes de editar, leer `AGENTS.md`. Los skills de investigacion, documentos, RAG, reproduccion, entrenamiento y debugging ya estan instalados en las carpetas de skills del proyecto.
