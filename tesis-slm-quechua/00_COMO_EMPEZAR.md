# Como Empezar El Proyecto SLM + RAG Quechua Collao

Este documento aterriza el plan de tesis en pasos concretos. La idea principal es no empezar entrenando. Primero construimos datos limpios, evaluacion fija y RAG. Despues decidimos si QLoRA aporta algo.

## 1. Decision De Modelo

### Modelo base principal

Usaremos como candidato principal:

```text
Qwen/Qwen2.5-3B-Instruct
```

Razones:

- Es un modelo causal de lenguaje, compatible con `AutoModelForCausalLM`.
- Tiene tamano manejable para pruebas locales.
- Puede recibir adaptadores LoRA/QLoRA con PEFT.
- Tiene version GGUF para inferencia local con llama.cpp/Ollama.
- Es mas realista que 7B para una GTX 1050 Ti de 4 GB.

### Por que no empezar con GGUF para entrenar

Hay dos formas del modelo:

```text
1. Hugging Face Transformers
   Uso: entrenamiento, LoRA, QLoRA, PEFT, TRL.
   Ejemplo: Qwen/Qwen2.5-3B-Instruct

2. GGUF / llama.cpp / Ollama
   Uso: inferencia offline rapida.
   Ejemplo: Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M
```

Regla:

```text
Para entrenar/adaptar: usar Transformers + PEFT.
Para ejecutar offline final: usar GGUF/Ollama/llama.cpp.
```

No se entrena directamente el GGUF. Si se entrena un LoRA, se entrena sobre el modelo Transformers y despues se evalua como adaptador. Si se necesita entrega final offline, se puede fusionar/exportar o mantener el flujo RAG con el modelo GGUF.

### Configuracion LoRA inicial

Para Qwen2.5-3B-Instruct se debe probar LoRA sobre capas lineales del Transformer. Configuracion inicial propuesta:

```python
from peft import LoraConfig, TaskType

lora_config = LoraConfig(
    r=8,
    lora_alpha=16,
    lora_dropout=0.05,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    ],
    task_type=TaskType.CAUSAL_LM,
)
```

Si la memoria falla, bajar a:

```text
r = 4
target_modules = ["q_proj", "v_proj"]
```

## 2. Flujo Real De Datos

Los datos no empiezan en el modelo. Empiezan en una carpeta de fuentes y un manifiesto.

### Paso A: colocar fuentes crudas

Todo documento original se coloca en:

```text
tesis-slm-quechua/datos/crudos/
```

Ejemplos:

```text
datos/crudos/minedu/comunicacion_3ro.pdf
datos/crudos/minedu/ciencia_4to.pdf
datos/crudos/glosarios/glosario_collao.xlsx
datos/crudos/corpus/orcotoma_collao_ocr.txt
datos/crudos/diccionarios/diccionario_collao.pdf
```

### Paso B: registrar cada fuente en CSV

Crear:

```text
tesis-slm-quechua/datos/manifiesto.csv
```

Columnas:

```csv
id,path,title,language,dialect,domain,grade,source_type,source_url,license_status,use_in_rag,use_in_train,use_in_eval,notes
```

Ejemplo:

```csv
minedu_com_3,datos/crudos/minedu/comunicacion_3ro.pdf,Comunicacion 3ro EIB,es-qu,collao,comunicacion,3,pdf,https://...,public,true,false,false,Material curricular
glosario_001,datos/crudos/glosarios/glosario_collao.xlsx,Glosario Quechua Collao,qu-es,collao,glossary,na,xlsx,,review_required,true,true,false,Requiere validacion
americasnlp_quy,datos/crudos/external/americasnlp_quy.tsv,AmericasNLP QUY,qu-es,chanka,transfer,na,tsv,https://...,research,false,false,false,No usar como Collao sin validacion
```

Regla importante:

```text
Si no esta en manifiesto.csv, no entra al sistema.
```

### Paso C: limpiar y normalizar

Entrada:

```text
datos/crudos/
datos/manifiesto.csv
```

Salida:

```text
datos/limpios/
```

Aqui se hace:

- extraccion de texto de PDF/DOCX/XLSX/CSV;
- limpieza de OCR;
- normalizacion minima;
- separacion por idioma;
- etiquetado dialectal;
- conservacion de fuente y pagina/seccion.

### Paso D: fragmentar para RAG

Entrada:

```text
datos/limpios/
```

Salida:

```text
datos/corpus_rag/chunks.jsonl
```

Cada linea sera un chunk:

```json
{"chunk_id":"minedu_com_3_0001","source_id":"minedu_com_3","text":"...","language":"es","dialect":"collao","domain":"comunicacion","grade":"3","source_ref":"p. 12","tokens_estimated":280}
```

Reglas:

- texto curricular: 250 a 400 tokens;
- glosario: una entrada por chunk;
- `top-k` final maximo: 3 a 5 chunks;
- no mezclar Chanka con Collao sin etiqueta.

## 3. Flujo De Evaluacion

Antes de probar modelos se crea un banco fijo:

```text
tesis-slm-quechua/datos/evaluacion/questions_seed.csv
```


Columnas:

```csv
id,question,language,dialect,domain,grade,expected_source_id,reference_answer_es,reference_answer_qu,evaluation_type
```

Minimo inicial:

```text
10 preguntas en espanol
10 preguntas en Quechua Collao
10 preguntas mixtas espanol-Quechua
```

Esto permite comparar:

```text
E1: modelo solo
E2: modelo + RAG
E3: modelo + reglas
E4: modelo + RAG + reglas
```

Si no tenemos preguntas fijas, no sabremos si el sistema mejora o solo parece mejorar.

## 4. Que Se Procesa Local Y Que Se Procesa En Colab

### Local en esta PC

Se hace local:

- inventario de fuentes;
- limpieza inicial;
- chunking;
- indice BM25;
- indice FAISS/Chroma si el corpus no es enorme;
- evaluacion E1-E4;
- pruebas con Ollama/llama.cpp;
- desarrollo del RAG.

### Colab/Kaggle/WSL2

Se usa para:

- QLoRA;
- pruebas con `bitsandbytes`;
- entrenar adaptadores;
- conversiones pesadas si la PC no alcanza.

No se usa Colab para el prototipo final. El prototipo final debe funcionar offline.

## 5. Flujo De Entrenamiento QLoRA

QLoRA no entra al inicio. Entra solo si se cumple:

```text
1. Ya existe RAG funcionando.
2. Ya corrimos E1-E4.
3. Tenemos al menos 100 ejemplos supervisados buenos.
4. Los datos de entrenamiento no son los mismos que evaluacion.
5. El objetivo es estilo/terminologia/uso de contexto, no memorizar conocimiento.
```

Formato recomendado de entrenamiento:

```jsonl
{"messages":[{"role":"system","content":"Eres un asistente educativo EIB..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}],"metadata":{"language":"mixed_es_qu","dialect":"collao","domain":"comunicacion","source_id":"..."}}
```

Carpeta:

```text
data/train/qlora_sft.jsonl
```

Salida:

```text
models/adapters/qwen2_5_3b_collao_lora/
```

No commitear adaptadores pesados.

## 6. Flujo Completo Del Sistema

```text
Usuario
  ↓
Deteccion de idioma
  ↓
Normalizacion ligera
  ↓
Retriever hibrido
  ├─ BM25
  └─ Embeddings + FAISS/Chroma
  ↓
Contexto corto con fuentes
  ↓
Prompt pedagogico
  ↓
Modelo local Qwen2.5-3B
  ↓
Respuesta con trazabilidad
  ↓
Metricas y logs
```

## 7. Donde Encaja La Pagina Web/PWA

La PWA no se hace al inicio. Debe ir en carpeta separada:

```text
tesis-slm-quechua/apps/pwa/
```

Pero solo despues de tener:

```text
1. RAG funcional.
2. Modelo local funcionando.
3. API local estable.
4. Experimentos E1-E4 medidos.
```

Arquitectura futura:

```text
apps/pwa/          interfaz de usuario
src/app/api/       API local del asistente
src/rag/           recuperacion
src/inference/     modelo local
data/rag_corpus/   base de conocimiento
models/            modelos/adaptadores locales
```

La PWA no debe depender de OpenAI/Gemini. Puede consumir una API local.

## 8. Primeras 5 Tareas Reales

Estas son las tareas por donde debemos empezar:

1. Crear `configs/project.yaml`.
2. Crear `data/manifest.csv`.
3. Crear `data/raw/README.md` explicando como poner fuentes.
4. Crear `data/eval/questions_seed.csv` con 30 preguntas semilla.
5. Crear scripts de limpieza y chunking.

No empezamos por entrenar.
No empezamos por la web.
No empezamos por descargar 7B.

## 9. Decision Practica Actual

Para esta tesis:

```text
Modelo de investigacion / entrenamiento:
Qwen/Qwen2.5-3B-Instruct

Modelo de inferencia offline:
Qwen/Qwen2.5-3B-Instruct-GGUF:Q4_K_M

RAG:
FAISS + BM25 al inicio

Fine-tuning:
PEFT/TRL con LoRA o QLoRA solo despues de E1-E4

Web/PWA:
fase posterior en apps/pwa/
```

