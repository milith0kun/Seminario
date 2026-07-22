# Asistente educativo offline español–Quechua Collao (SLM + RAG)

Prototipo de tesis: asistente **textual y offline** para Educación Intercultural Bilingüe (EIB), con modelo compacto cuantizado, RAG local, recursos lingüísticos y QLoRA opcional.

**Convención del repo:** nombres de carpetas, scripts, configs y documentación en **español** cuando sea posible. IDs de modelos, librerías y formatos estándar (GGUF, JSONL, YAML) se mantienen en su forma técnica habitual.

---

## 1. Qué es este proyecto

| Aspecto | Valor |
|---------|--------|
| Objetivo | Responder consultas curriculares en español y Quechua Collao sin internet |
| Modelo offline | `Qwen2.5-3B-Instruct` en GGUF Q4_K_M |
| Recuperación | RAG local (BM25 ahora; embeddings listos para FAISS) |
| Alcance pedagógico | 3.°–6.° primaria, Comunicación y Ciencia y Tecnología |
| Dialecto | Solo **Quechua Collao** (no mezclar Chanka sin etiqueta) |
| Hardware de referencia | GTX 1050 Ti 4 GB VRAM, Windows, Python 3.11 |
| Tesis LaTeX | Carpeta hermana `../Plan de Tesis/` |

---

## 2. Inicio rápido

```bash
# Git Bash (recomendado en este PC)
cd /d/Proyectos/Seminario/tesis-slm-quechua
source .venv/Scripts/activate

# Verificar / descargar modelos
python scripts/descargar_recursos.py

# Prueba de humo del modelo
python scripts/prueba_humo_modelo.py

# Chat por terminal
python scripts/chat.py
python scripts/chat.py --rag

# Servidor web + API (puerto 8000)
python scripts/lanzar_servidor.py

# Experimento E1 (línea base)
python scripts/ejecutar_e1.py --limit=3

# Regenerar fragmentos RAG desde el manifiesto
python -m src.ingesta.construir_fragmentos

# Pruebas unitarias
pytest
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

---

## 3. Estructura de carpetas

```text
tesis-slm-quechua/
├── apps/
│   ├── pwa/                 # Fork de mlc-ai/web-llm-chat: chat + RAG 100% en el navegador (WebLLM)
│   └── pwa_legado/          # PWA custom anterior (cliente HTTP hacia servidor_api.py), resguardada
├── configuraciones/         # YAML del sistema
├── cuadernos/               # Jupyter (exploración)
├── datos/
│   ├── crudos/              # Fuentes originales
│   │   ├── muestras/        # Textos de prueba locales
│   │   └── external/        # Datasets externos (etiquetar dialecto)
│   ├── limpios/             # Texto normalizado
│   ├── corpus_rag/          # chunks.jsonl para recuperación
│   ├── evaluacion/          # Banco de preguntas
│   ├── entrenamiento/       # Datos SFT / telemetría
│   ├── sinteticos/          # Pares generados (futuro)
│   └── manifiesto.csv        # Inventario obligatorio de fuentes
├── documentacion/
│   ├── ESTADO_ACTUAL.md     # Snapshot de avance
│   ├── decisiones/          # ADRs técnicos
│   └── planes/              # Roadmap por fases
├── experimentos/            # E1 … E6 y salidas JSONL
├── modelos/                 # Pesos locales (NO van a git)
│   ├── gguf/                # Inferencia offline
│   ├── base/                # HF para QLoRA futuro
│   ├── embeddings/          # Vectores multilingües
│   └── adaptadores/         # LoRA entrenados (futuro)
├── pruebas/                 # pytest
├── reportes/                # Humo y reportes
├── scripts/                 # CLI ejecutable
├── src/                     # Código Python del prototipo
│   ├── comun/
│   ├── ingesta/
│   ├── rag/
│   ├── inferencia/
│   ├── aplicacion/          # API FastAPI + interfaz estática
│   ├── evaluacion/          # (pendiente)
│   └── ajuste_fino/         # (pendiente QLoRA)
├── tesis/                   # Material adjunto
├── .venv/                   # Entorno virtual
├── 00_COMO_EMPEZAR.md
├── PROJECT_INIT.md
├── pytest.ini
└── requirements*.txt
```

---

## 4. Configuraciones (`configuraciones/`)

| Archivo | Para qué sirve |
|---------|----------------|
| `proyecto.yaml` | Nombre del proyecto, par de lenguas, grados, dominios, hardware, rutas |
| `modelos.yaml` | ID HF, ruta GGUF, `n_ctx`, hilos, temperatura, prompt de humo |
| `rag.yaml` | Tamaño de chunks, top-k, modelo de embeddings y ruta local |
| `evaluacion.yaml` | Banco de preguntas, métricas y lista de experimentos |

Carga en código: `src.comun.rutas.cargar_yaml("modelos.yaml")`.

---

## 5. Modelos locales (`modelos/`)

| Uso | Ruta | Tamaño aprox. | Estado |
|-----|------|---------------|--------|
| Inferencia offline / chat / API | `modelos/gguf/qwen2.5-3b-instruct-q4_k_m.gguf` | ~2.0 GB | Descargado |
| Investigación / QLoRA futuro | `modelos/base/Qwen2.5-3B-Instruct/` | ~5.8 GB | Descargado |
| Embeddings RAG denso | `modelos/embeddings/sentence-transformers__paraphrase-multilingual-MiniLM-L12-v2/` | ~0.45 GB | Descargado |
| Adaptadores LoRA | `modelos/adaptadores/` | — | Vacío |

Orígenes Hugging Face:

- `Qwen/Qwen2.5-3B-Instruct-GGUF`
- `Qwen/Qwen2.5-3B-Instruct`
- `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

**No commitear** `.gguf`, `.safetensors` ni `.venv` (ver `.gitignore`).

Descarga:

```bash
python scripts/descargar_recursos.py              # todo
python scripts/descargar_recursos.py --only gguf
python scripts/descargar_recursos.py --only hf
python scripts/descargar_recursos.py --only embeddings
python scripts/descargar_modelo.py                # solo GGUF
```

---

## 6. Datos (`datos/`)

### 6.1 Manifiesto (`datos/manifiesto.csv`)

Toda fuente debe registrarse aquí. Si no está en el manifiesto, **no entra** al RAG ni al entrenamiento.

Columnas:

```text
id, path, title, language, dialect, domain, grade,
source_type, source_url, license_status,
use_in_rag, use_in_train, use_in_eval, notes
```

### 6.2 Archivos de datos actuales

| Archivo / carpeta | Descripción |
|-------------------|-------------|
| `datos/crudos/muestras/ciencia_fotosintesis_es.txt` | Muestra curricular (prueba) |
| `datos/crudos/muestras/glosario_collao_sample.txt` | Glosario de prueba |
| `datos/crudos/external/` | AmericasNLP, LlamaCha, etc. (etiquetar dialecto) |
| `datos/corpus_rag/chunks.jsonl` | Fragmentos indexables (uno por línea JSON) |
| `datos/evaluacion/questions_seed.csv` | 30 preguntas semilla (es / qu / mixto) |
| `datos/entrenamiento/telemetria_interacciones.jsonl` | Feedback like/dislike desde la API |

### 6.3 Esquema de un chunk (JSONL)

```json
{
  "chunk_id": "sample_ciencia_foto_0001",
  "source_id": "sample_ciencia_foto",
  "text": "...",
  "language": "es",
  "dialect": "collao",
  "domain": "ciencia_y_tecnologia",
  "grade": "4",
  "source_ref": "...",
  "tokens_estimated": 280
}
```

---

## 7. Código fuente (`src/`)

### 7.1 `src/comun/` — rutas y config

| Archivo | Símbolos | Descripción |
|---------|----------|-------------|
| `rutas.py` | `ROOT`, `CONFIGURACIONES`, `DATOS`, `MODELOS`, `EXPERIMENTOS`, `REPORTES`, `SRC` | Rutas absolutas del proyecto |
| | `cargar_yaml(nombre)` | Lee un YAML de `configuraciones/` |
| | `load_yaml(name)` | Alias en inglés de compatibilidad |

### 7.2 `src/ingesta/` — limpieza y fragmentación

| Archivo | Función / clase | Descripción |
|---------|-----------------|-------------|
| `limpiar_texto.py` | `clean_text(text)` | Normaliza espacios, saltos de línea y NBSP |
| | `estimate_tokens(text)` | Estimación simple de tokens (~1.3 × palabras) |
| `fragmentar_documentos.py` | `chunk_prose(...)` | Fragmenta prosa (250–400 tokens, solape) |
| | `chunk_glossary_line(...)` | Una entrada de glosario = un chunk |
| | `write_jsonl(chunks, path)` | Escribe `chunks.jsonl` |
| `construir_fragmentos.py` | `main()` | Lee manifiesto + crudos → `datos/corpus_rag/chunks.jsonl` |

```bash
python -m src.ingesta.construir_fragmentos
```

### 7.3 `src/rag/` — recuperación

| Archivo | Función / clase | Descripción |
|---------|-----------------|-------------|
| `indice_bm25.py` | `tokenize(text)` | Tokeniza para BM25 |
| | `BM25Index` | Índice léxico sobre chunks |
| | `BM25Index.from_jsonl(path)` | Carga desde JSONL |
| | `BM25Index.search(query, top_k)` | Devuelve chunks con `score` |
| `constructor_contexto.py` | `build_context(chunks, max_chunks)` | Arma texto de contexto con `source_id` |

### 7.4 `src/inferencia/` — idioma, prompts y modelo

| Archivo | Función / clase | Descripción |
|---------|-----------------|-------------|
| `enrutador_lenguaje.py` | `detect_language(text)` | Devuelve `es`, `qu_collao`, `mixed_es_qu` o `unknown` |
| `plantillas_prompt.py` | `SYSTEM_EIB`, `SYSTEM_WITH_CONTEXT` | System prompts pedagógicos |
| | `build_messages(user_text, context, language)` | Mensajes chat (system + user) |
| `ejecutor_modelo.py` | `GenerationResult` | Dataclass: texto, latencia, tps, error |
| | `ModelRunner` | Carga GGUF con `llama-cpp` y genera |
| | `ModelRunner.ensure_model()` | Verifica que exista el archivo GGUF |
| | `ModelRunner.generate(...)` | Inferencia chat completion |
| | `EjecutorModelo` | Alias en español de `ModelRunner` |

### 7.5 `src/aplicacion/` — API y web

| Archivo | Símbolo | Descripción |
|---------|---------|-------------|
| `servidor_api.py` | `app` | App FastAPI |
| | `get_local_ip()` | IP LAN para acceso desde el celular |
| | `init_services()` | Carga perezosa de modelo + BM25 |
| | `ChatRequest` | Body: `pregunta`, `modo`, `idioma` |
| | `TelemetriaRequest` | Body: valoración like/dislike + corrección |
| | `obtener_estado` | `GET /api/estado` |
| | `procesar_chat` | `POST /api/chat` |
| | `guardar_telemetria` | `POST /api/telemetria` |
| `interfaz/` | (estáticos) | UI servida por FastAPI si existe |

#### Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| `GET` | `/api/estado` | Salud, IP, modelo, nº de chunks, modos |
| `POST` | `/api/chat` | Genera respuesta (modos E1–E4) |
| `POST` | `/api/telemetria` | Guarda feedback en JSONL |

Modos de chat:

| Modo | Comportamiento |
|------|----------------|
| `E1_base` | Solo modelo |
| `E2_rag` | Modelo + RAG |
| `E3_reglas` | Modelo + reglas/prompt (sin RAG) |
| `E4_rag_reglas` | Modelo + RAG + reglas (por defecto) |

### 7.6 Carpetas aún vacías / pendientes

| Carpeta | Uso futuro |
|---------|------------|
| `src/evaluacion/` | Métricas chrF++, RAGAS, Recall@k, rúbricas |
| `src/ajuste_fino/` | Dataset y entrenamiento QLoRA |
| `modelos/adaptadores/` | Pesos LoRA resultantes |

---

## 8. Scripts CLI (`scripts/`)

| Script | Función principal | Uso |
|--------|-------------------|-----|
| `descargar_modelo.py` | `download_gguf()` | Solo descarga el GGUF |
| `descargar_recursos.py` | `download_gguf`, `download_hf_base`, `download_embeddings` | Todos los pesos locales |
| `descargar_datasets_externos.py` | `descargar_americasnlp`, `descargar_llamacha` | Datos externos de referencia |
| `prueba_humo_modelo.py` | `main()` | Smoke test → `reportes/pruebas_humo/` |
| `chat.py` | `main()` | Chat terminal; flag `--rag` |
| `ejecutar_e1.py` | `main()` | Corre E1 sobre preguntas seed (`--limit=N`, `--all`) |
| `lanzar_servidor.py` | `main()` | Uvicorn en `0.0.0.0:8000` |

Ejemplos:

```bash
python scripts/chat.py --rag
python scripts/ejecutar_e1.py --limit=5
python scripts/ejecutar_e1.py --all
python scripts/lanzar_servidor.py
# luego abrir http://localhost:8000
```

---

## 9. Experimentos (`experimentos/`)

| Carpeta | Configuración de tesis | Estado |
|---------|------------------------|--------|
| `E1_base/` | Solo modelo | Parcial (hay salidas de prueba) |
| `E2_rag/` | Modelo + RAG | Pendiente |
| `E3_rules/` / `E3_reglas` | Modelo + reglas | Pendiente |
| `E4_rag_rules/` | RAG + reglas | Pendiente |
| `E5_qlora/` | Adaptador QLoRA | Opcional / puerta de factibilidad |
| `E6_hybrid/` | RAG + QLoRA + reglas | Opcional |

Salidas típicas: `experimentos/E1_base/salidas/ejecucion_YYYYMMDD_HHMMSS.jsonl`

---

## 10. Pruebas (`pruebas/`)

Configuradas en `pytest.ini` (`testpaths = pruebas`).

| Archivo | Qué valida |
|---------|------------|
| `test_limpiar_texto.py` | `clean_text`, `estimate_tokens` |
| `test_fragmentar_documentos.py` | `chunk_prose`, glosario |
| `test_enrutador_lenguaje.py` | `detect_language` |
| `test_servidor_api.py` | Endpoints / contratos API |

```bash
pytest
pytest pruebas/test_limpiar_texto.py -q
```

---

## 11. Dependencias

| Archivo | Contenido |
|---------|-----------|
| `requirements.txt` | Apunta a `requirements-core.txt` |
| `requirements-inference.txt` | Mínimo para GGUF + RAG + tests (`llama-cpp-python`, `sentence-transformers`, etc.) |
| `requirements-core.txt` | Stack amplio (torch, transformers, faiss, ragas, …) |
| `requirements-qlora-wsl.txt` | QLoRA en WSL2/Colab (`bitsandbytes`, peft, …) |

```bash
pip install -r requirements-inference.txt
```

---

## 12. Documentación adicional

| Documento | Contenido |
|-----------|-----------|
| [`documentacion/ESTADO_ACTUAL.md`](documentacion/ESTADO_ACTUAL.md) | Qué hay hoy, tamaños, evidencias, pendientes |
| [`00_COMO_EMPEZAR.md`](00_COMO_EMPEZAR.md) | Flujo de trabajo y decisiones de stack |
| [`documentacion/planes/2026-07-06-roadmap-prototipo-slm-rag.md`](documentacion/planes/2026-07-06-roadmap-prototipo-slm-rag.md) | Roadmap por fases |
| [`documentacion/decisiones/0001-alcance-y-hardware.md`](documentacion/decisiones/0001-alcance-y-hardware.md) | Hardware y restricciones |
| [`PROJECT_INIT.md`](PROJECT_INIT.md) | Prompt de inicialización para agentes |
| [`datos/crudos/README.md`](datos/crudos/README.md) | Cómo colocar fuentes crudas |

Instrucciones de agentes del monorepo: `../AGENTS.md`.

---

## 13. Flujo del sistema

```text
Usuario (chat CLI / API / PWA)
        │
        ▼
 detect_language  ──►  es | qu_collao | mixed_es_qu
        │
        ▼
  [opcional] BM25Index.search  ──►  build_context
        │
        ▼
 build_messages (prompt EIB + contexto)
        │
        ▼
 ModelRunner.generate  (GGUF / llama-cpp)
        │
        ▼
 Respuesta + latencia + (telemetría opcional)
```

---

## 14. Reglas de trabajo

1. **No entrenar desde cero.** Solo adaptar (QLoRA) si E1–E4 ya están medidos.
2. **No mezclar dialectos** sin etiqueta (`collao` / `chanka` / `cusco` / `unknown`).
3. **Si no está en `manifiesto.csv`, no entra al sistema.**
4. **Chunks cortos** (250–400 tokens; glosario = 1 entrada) y `top-k` 3–5.
5. **No commitear** modelos, `.venv`, `node_modules` ni datos privados de validación.
6. **Separar commits** de `Plan de Tesis/` y del prototipo técnico.
7. **PWA Next.js** (`apps/pwa/`) es fase de interfaz; el núcleo offline es Python + GGUF.

---

## 15. Estado resumido

| Componente | Estado |
|------------|--------|
| GGUF offline + smoke test | Listo (~13 tok/s CPU) |
| HF base + embeddings | Descargados |
| Ingesta + BM25 + chat CLI | Listo |
| API FastAPI | Listo |
| Banco 30 preguntas | Listo |
| Datos curriculares reales MINEDU | Pendiente |
| RAG denso FAISS | Embeddings listos; cableado pendiente |
| E1–E4 completos + métricas | Pendiente |
| QLoRA | No iniciado (pesos HF listos) |

Detalle vivo: **`documentacion/ESTADO_ACTUAL.md`**.
