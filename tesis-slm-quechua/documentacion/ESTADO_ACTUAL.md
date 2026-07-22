# Estado Actual Del Prototipo

**Fecha:** 2026-07-21  
**Proyecto:** Asistente educativo offline español–Quechua Collao (SLM + RAG)  
**Carpeta:** `tesis-slm-quechua/`

---

## 1. Resumen en una frase

Ya hay un prototipo local usable: modelo GGUF cargado, chat CLI, RAG BM25 de prueba, banco de 30 preguntas, prueba de humo OK (~13 tok/s en CPU) y modelos HF/embeddings descargados para las siguientes fases.

---

## 2. Qué está listo

| Componente | Estado | Detalle |
|------------|--------|---------|
| Entorno Python 3.11 + `.venv` | Listo | Dependencias de inferencia instaladas |
| Configuración YAML | Listo | `configuraciones/*.yaml` |
| Modelo GGUF offline | Listo | Qwen2.5-3B-Instruct Q4_K_M (~2.0 GB) |
| Modelo HF base | Listo | Para QLoRA futuro (~5.8 GB) |
| Embeddings multilingües | Listo | MiniLM-L12-v2 (~450 MB pesos) |
| Inferencia local (`llama-cpp`) | Listo | CPU, ~12–13 tok/s |
| Chat interactivo | Listo | Con y sin RAG |
| Enrutador de idioma | Listo | es / qu_collao / mixed / unknown |
| Plantillas de prompt EIB | Listo | Con/sin contexto |
| Limpieza y chunking | Listo | Prosa + glosario |
| RAG BM25 | Listo | Sobre chunks de muestra |
| RAG denso (FAISS) | Pendiente de cablear | Embeddings ya descargados |
| Manifiesto de fuentes | Listo (muestra) | 2 fuentes de prueba |
| Banco de evaluación | Listo | 30 preguntas semilla |
| Prueba de humo | OK | ~4.7 s, sin error |
| Tests unitarios | OK | 7 passed |
| Experimento E1 | Parcial | 1 corrida corta (2 ítems) |
| E2–E6 | No iniciados | Carpetas vacías |
| Datos curriculares reales MINEDU | No | Solo muestras sintéticas locales |
| QLoRA / adaptadores | No | Aún no toca |
| PWA / interfaz web | En progreso | Chat 100% en el navegador (WebLLM), ver sección 14 |

---

## 3. Modelos descargados (dónde están)

Ruta raíz: `tesis-slm-quechua/modelos/`

```text
modelos/
├── gguf/
│   └── qwen2.5-3b-instruct-q4_k_m.gguf     # 2.0 GB  → chat / E1–E4 offline
├── base/
│   └── Qwen2.5-3B-Instruct/                # 5.8 GB  → QLoRA futuro (Transformers)
├── embeddings/
│   └── sentence-transformers__paraphrase-multilingual-MiniLM-L12-v2/
│                                           # ~0.45 GB pesos (+ cache) → RAG denso
└── adaptadores/                            # vacío (futuros LoRA)
```

| ID Hugging Face | Uso local | Archivo/carpeta |
|-----------------|-----------|-----------------|
| `Qwen/Qwen2.5-3B-Instruct-GGUF` | Inferencia offline | `modelos/gguf/qwen2.5-3b-instruct-q4_k_m.gguf` |
| `Qwen/Qwen2.5-3B-Instruct` | Investigación / QLoRA | `modelos/base/Qwen2.5-3B-Instruct/` |
| `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | Embeddings RAG | `modelos/embeddings/...` |

**Total en disco (modelos):** ~8.5 GB  
**No se versionan en Git** (ver `.gitignore`).

### Evidencia de humo (última corrida)

- Archivo: `reportes/pruebas_humo/smoke_model.json`
- Backend: `llama_cpp`
- Latencia: ~4670 ms
- Velocidad: ~12.8 tokens/s
- Error: ninguno

---

## 4. Estructura del repositorio técnico

```text
tesis-slm-quechua/
├── configuraciones/     # proyecto, modelos, rag, evaluacion
├── datos/
│   ├── crudos/          # fuentes originales (+ muestras)
│   ├── limpios/
│   ├── corpus_rag/      # chunks.jsonl
│   ├── evaluacion/      # questions_seed.csv (30)
│   ├── entrenamiento/
│   ├── sinteticos/
│   └── manifiesto.csv
├── documentacion/
│   ├── decisiones/      # 0001 hardware/alcance
│   ├── planes/          # roadmap completo
│   └── ESTADO_ACTUAL.md # este archivo
├── experimentos/        # E1…E6
├── modelos/             # pesos locales (no git)
├── pruebas/             # pytest
├── reportes/
├── scripts/             # CLI
├── src/
│   ├── comun/
│   ├── ingesta/
│   ├── rag/
│   ├── inferencia/
│   ├── evaluacion/      # vacío
│   ├── ajuste_fino/     # vacío
│   └── aplicacion/      # vacío
├── .venv/
└── requirements*.txt
```

La tesis LaTeX vive aparte en `Plan de Tesis/` (raíz del monorepo Seminario).

---

## 5. Código implementado

### `src/`

| Módulo | Archivos | Función |
|--------|----------|---------|
| `comun` | `rutas.py` | Rutas del proyecto + carga YAML |
| `ingesta` | `limpiar_texto.py`, `fragmentar_documentos.py`, `construir_fragmentos.py` | Limpieza, chunks, build desde manifiesto |
| `rag` | `indice_bm25.py`, `constructor_contexto.py` | Recuperación léxica + armado de contexto |
| `inferencia` | `ejecutor_modelo.py`, `enrutador_lenguaje.py`, `plantillas_prompt.py` | GGUF chat, idioma, prompts EIB |

### `scripts/`

| Script | Qué hace |
|--------|----------|
| `descargar_modelo.py` | Solo GGUF |
| `descargar_recursos.py` | GGUF + HF base + embeddings |
| `descargar_datasets_externos.py` | Datasets externos (si aplica) |
| `prueba_humo_modelo.py` | Smoke test → `reportes/pruebas_humo/` |
| `chat.py` | Chat CLI (`--rag` opcional) |
| `ejecutar_e1.py` | Baseline E1 sobre preguntas seed |

### Configuración

| Archivo | Contenido |
|---------|-----------|
| `configuraciones/proyecto.yaml` | Alcance EIB, hardware, paths |
| `configuraciones/modelos.yaml` | GGUF, HF, smoke prompt |
| `configuraciones/rag.yaml` | Chunking, top-k, embeddings |
| `configuraciones/evaluacion.yaml` | Métricas y experimentos |

---

## 6. Datos actuales

| Recurso | Cantidad | Notas |
|---------|----------|-------|
| Fuentes en manifiesto | 2 | Muestras locales (no MINEDU oficial) |
| Chunks RAG | 10 | `datos/corpus_rag/chunks.jsonl` |
| Preguntas seed | 30 | es / qu_collao / mixed |
| AmericasNLP u otros | Carpeta `datos/crudos/external/` | Tratar como no-Collao si se usan |
| Corpus Orcotoma / glosarios reales | No integrados aún | Pendiente de curación |

**Regla:** si no está en `datos/manifiesto.csv`, no entra al sistema.

---

## 7. Hardware y decisiones técnicas

Documentado en `documentacion/decisiones/0001-alcance-y-hardware.md`:

- GPU: NVIDIA GTX 1050 Ti, 4 GB VRAM
- Inferencia actual: **CPU** (`n_gpu_layers: 0`)
- Modelo por defecto offline: **Qwen2.5-3B Q4_K_M**
- QLoRA: solo WSL2 / Colab / Kaggle; no nativo Windows
- Prototipo **textual**, offline, sin voz
- Dialecto objetivo: **Quechua Collao** (no mezclar Chanka sin etiqueta)

---

## 8. Cómo ejecutarlo (bash / Git Bash)

```bash
cd /d/Proyectos/Seminario/tesis-slm-quechua
source .venv/Scripts/activate

# Verificar / re-descargar assets
python scripts/descargar_recursos.py

# Prueba de humo
python scripts/prueba_humo_modelo.py

# Chat solo modelo (E1 mental)
python scripts/chat.py

# Chat con RAG BM25
python scripts/chat.py --rag

# Experimento E1 (pocas preguntas)
python scripts/ejecutar_e1.py --limit=3

# Regenerar chunks desde manifiesto
python -m src.ingesta.construir_fragmentos

# Tests
pytest
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 9. Alineación con la tesis

| Objetivo de tesis | Estado técnico |
|-------------------|----------------|
| Asistente offline ES–Quechua Collao | Base de inferencia lista |
| SLM cuantizado | GGUF Q4_K_M operativo |
| RAG local disciplinado | BM25 + chunks cortos (muestra) |
| Detección de idioma | Heurística inicial |
| Comparar E1 / E2 / E3 (híbrido) | Solo E1 parcial |
| Métricas técnicas / lingüísticas / pedagógicas | Definidas en YAML; no pipeline completo |
| QLoRA opcional | Pesos HF listos; sin entrenamiento |
| Materiales EIB reales | Pendiente |

---

## 10. Qué falta (orden recomendado)

1. **Curar datos reales** (MINEDU EIB, glosarios Collao, corpus validados) → manifiesto.
2. **Regenerar chunks** y medir Recall@k sobre el banco seed.
3. **Cablear RAG denso** (FAISS + embeddings locales ya descargados).
4. **Correr E1 completo** (30 preguntas) y guardar JSONL.
5. **Correr E2** (modelo + RAG) y comparar con E1.
6. **E3/E4** (reglas / RAG+reglas).
7. **Puerta QLoRA** solo si E1–E4 están medidos y hay ≥100 ejemplos supervisados.
8. **PWA** solo después de API local estable.

---

## 11. Dependencias instaladas (inferencia)

Paquetes clave en `.venv`:

- `llama-cpp-python` (inferencia GGUF)
- `huggingface_hub`, `pyyaml`
- `sentence-transformers`, `faiss-cpu`, `rank-bm25`
- `torch` (CPU), `transformers`
- `sacrebleu`, `evaluate`, `pandas`, `pytest`

Archivos:

- `requirements-inference.txt` — mínimo para chat/RAG
- `requirements-core.txt` — stack amplio (LangChain, RAGAS, etc.; no todo instalado aún)
- `requirements-qlora-wsl.txt` — bitsandbytes/peft en WSL

---

## 12. Artefactos de evidencia existentes

| Artefacto | Ruta |
|-----------|------|
| Smoke test | `reportes/pruebas_humo/smoke_model.json` |
| E1 parcial | `experimentos/E1_base/salidas/ejecucion_20260721_192559.jsonl` |
| Chunks muestra | `datos/corpus_rag/chunks.jsonl` |
| Preguntas | `datos/evaluacion/questions_seed.csv` |

---

## 13. No hacer todavía

- Entrenar desde cero
- Descargar 7B como default
- Mezclar Quechua Chanka como si fuera Collao
- Commitear modelos (`.gguf`, `.safetensors`) ni `.venv`

> Nota: la regla original "empezar PWA antes de E1–E4" se adelantó por decisión
> explícita (2026-07-21) para tener una interfaz cliente-only demostrable.
> Los experimentos E1–E4 formales siguen corriendo por CLI Python
> (`scripts/ejecutar_e1.py`), independientes de la PWA — ver sección 14.

---

## 14. PWA: chat + RAG 100% en el navegador (WebLLM)

**Carpeta:** `apps/pwa/` — fork de [`mlc-ai/web-llm-chat`](https://github.com/mlc-ai/web-llm-chat) (Apache-2.0), clonado y adaptado el 2026-07-21. La PWA custom anterior (llamaba a un backend Python por HTTP) quedó resguardada en `apps/pwa_legado/`.

**Arquitectura:** el modelo y el RAG corren enteramente en el dispositivo del usuario (navegador), sin depender de `src/aplicacion/servidor_api.py`. Hay **dos motores de inferencia**, con degradación automática:

| Pieza | Dónde | Equivalente Python |
|-------|-------|---------------------|
| Motor GPU (preferido) | `app/client/webllm.ts` — `@mlc-ai/web-llm`, catálogo Qwen2.5-Instruct 0.5B–7B (`q4f16_1`/`q4f32_1`), requiere WebGPU | `src/inferencia/ejecutor_modelo.py` |
| Motor CPU (respaldo) | `app/client/wllama.ts` — `@wllama/wllama` (WASM, `llama.cpp`), Qwen2.5-Instruct 0.5B/1.5B en `.gguf` (mismo formato que el lado Python), sin requisito de GPU | — (nuevo, no existía en Python) |
| Enrutador de idioma | `app/rag/enrutadorLenguaje.ts` (puerto literal), aplicado en `app/store/chat.ts` como instrucción invisible al modelo | `src/inferencia/enrutador_lenguaje.py` |
| Prompt EIB | `app/constant.ts` (`DEFAULT_SYSTEM_TEMPLATE`, inyectado globalmente) | `src/inferencia/plantillas_prompt.py` |
| RAG | `app/rag/index.ts` (`buscarRAGLocal`/`construirContextoRAG`, Fuse.js sobre `public/chunks.json`), invocado dentro de `chatCompletion()` de **ambos** motores (invisible en la burbuja del usuario) | `src/rag/indice_bm25.py` + `constructor_contexto.py` |
| Selección/descarga del modelo | Botón con el modelo activo en la barra de acciones del chat (`ChatAction` en `app/components/chat.tsx`) abre `ModelSelect`; catálogo mostrado depende de qué motor esté activo | — |

**Catálogo de modelos GPU** recortado en `app/constant.ts` a solo la familia Qwen2.5-Instruct (0.5B/1.5B/3B/7B), quitando las demás familias del `web-llm-chat` original (Phi, Llama, Gemma, Mistral, DeepSeek, etc.). Proveedor único WebLLM además del respaldo CPU (se quitó el selector "MLC-LLM REST API", que dependía de un endpoint remoto).

**Modelo por defecto alineado con la tesis** (verificado contra `documentacion/decisiones/0001-alcance-y-hardware.md` y `Plan de Tesis/partes/05bFactibilidad.tex`, que fijan "Qwen2.5-3B-Instruct" como *"modelo local por defecto"* y 7B como *"variante de calidad solo si hay RAM suficiente"*): `DEFAULT_MODEL` en `app/store/config.ts` es `Qwen2.5-3B-Instruct-q4f32_1-MLC`; el catálogo CPU (`DEFAULT_WLLAMA_MODELS`) tiene al 3B primero (mismo criterio). 0.5B/1.5B no están en la tesis — se mantienen solo como alternativas livianas opcionales. El 7B se excluyó del catálogo CPU porque su `.gguf` (~4.7 GB) supera el límite de 2 GB por archivo de `wllama`; sigue disponible del lado GPU.

**Degradación automática a CPU** (`app/components/home.tsx`, `app/store/chat.ts`): si el dispositivo no tiene `navigator.gpu` en absoluto, arranca directo en modo CPU. Si tiene WebGPU pero falla al generar (`GPUPipelineError`/`ShaderModule` inválido — típico de GPUs sin soporte de la extensión `shader-f16`), primero se reintenta con un motor GPU alternativo (`WebWorker` en vez de `ServiceWorker`); si vuelve a fallar igual, se pasa automáticamente al motor CPU (`wllama`) en la siguiente recarga — sin intervención manual del usuario.

**Dónde y cómo se guardan los modelos descargados** (no son archivos visibles como en `modelos/` del lado Python — viven dentro del almacenamiento del navegador para ese sitio):

| Motor | Mecanismo de caché | Dónde se ve en DevTools |
|-------|---------------------|--------------------------|
| GPU (`@mlc-ai/web-llm`) | `ArtifactCache`/`ArtifactIndexedDBCache` interno de la librería (Cache API por defecto, o IndexedDB si `cacheType = index_db`) | Application → Cache Storage (o IndexedDB) → buckets `webllm/model`, `webllm/config`, etc. |
| CPU (`@wllama/wllama`) | `CacheManager` interno de la librería, también sobre Cache API | Application → Cache Storage → buckets propios de wllama |

Ambos son independientes del Service Worker de la PWA: los pesos se descargan de Hugging Face (origen distinto) y cada librería los cachea por su cuenta la primera vez; después cargan casi instantáneo sin red. Borrar "datos del sitio" en el navegador borra también estos modelos (hay que volver a descargarlos).

**Corrección para que funcione realmente offline**: el corpus RAG (`public/chunks.json`) y el binario WASM del motor CPU (`public/wllama/wllama.wasm`) son parte de la propia app, servidos por el Service Worker (`app/worker/service-worker.ts`) — pero la estrategia por defecto que trae `@serwist/next` (`NetworkOnly` para rutas no reconocidas) hacía que fallaran si el usuario estaba realmente sin conexión, aunque el modelo ya estuviera cacheado. Se agregó una regla `CacheFirst` explícita para `/chunks.json`, `/rag/*` y `/wllama/*` — quedan disponibles offline después de la primera carga, igual que los pesos del modelo.

**Pendiente / conocido:**
- El corpus RAG se sirve desde `public/chunks.json` (copiado/convertido a mano desde `datos/corpus_rag/chunks.jsonl`); no hay build step que lo sincronice todavía.
- El motor CPU no tiene cancelación real de generación en curso más allá de un `AbortSignal` (best-effort).
- El motor CPU corre en single-thread WASM (el hosting como export estático no puede setear los headers COOP/COEP que necesita el modo multi-hilo) — funcional pero lento; aceptable como respaldo de compatibilidad, no como modo principal.
- No se ha probado en un navegador real con GPU sin `shader-f16` ni en un dispositivo sin WebGPU dentro de esta sesión — falta confirmar en hardware real que la degradación a CPU efectivamente genera respuestas.
- La telemetría (`/api/telemetria`) sigue apuntando al backend Python `servidor_api.py`, ahora opcional/best-effort desde `apps/pwa_legado`; **no está reconectada en el nuevo `apps/pwa`** todavía (no hay pantalla de feedback like/dislike en el fork de web-llm-chat).

---

*Documento vivo: actualizar este archivo cuando cambie el estado de modelos, datos o experimentos.*
