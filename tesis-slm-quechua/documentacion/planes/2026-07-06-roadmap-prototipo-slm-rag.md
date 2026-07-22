# Plan De Implementacion Del Prototipo SLM + RAG Quechua Collao

**Objetivo:** construir un prototipo reproducible de asistente educativo offline espanol-Quechua Collao, alineado con el plan de tesis.

**Arquitectura:** el prototipo se organiza como un pipeline local modular: curacion de datos, normalizacion con control dialectal, recuperacion hibrida, generacion con prompts controlados, inferencia local con SLM, registro de experimentos y evaluacion multidimensional. QLoRA es opcional y solo debe iniciarse despues de medir una linea base RAG funcional.

**Stack tecnico:** Python 3.11, FAISS/ChromaDB, BM25, sentence-transformers, Transformers/PEFT/TRL, Ollama o llama.cpp/GGUF, RAGAS, SacreBLEU, BERTScore y pytest.

---

## Alineacion Con La Tesis

El plan de tesis exige:

- Asistente offline espanol-Quechua Collao para contextos EIB.
- Prototipo textual, sin voz.
- Modelo base: Qwen2.5-3B como opcion local segura; 7B solo como variante de calidad si el hardware lo permite.
- RAG local con fragmentos cortos y `top-k` pequeno.
- Glosarios, diccionarios y reglas de normalizacion explicitas.
- Comparacion de configuraciones E1-E6.
- Evaluacion tecnica, linguistica, pedagogica y de recuperacion.
- No entrenar desde cero.
- QLoRA solo como rama experimental acotada para estilo, terminologia o uso del contexto RAG.

## Limites Del Repositorio

- `Plan de Tesis/`: fuentes LaTeX, capitulos, bibliografia y documentos academicos. No editar durante la implementacion tecnica salvo que se pida explicitamente actualizar la tesis.
- `tesis-slm-quechua/`: codigo, datos, modelos, experimentos, reportes y archivos de reproducibilidad.
- `.agents/skills/`, `.agent/skills/`, `.claude/skills/`: capacidades de agentes. No modificar salvo instalacion o actualizacion de skills.

## Estructura Tecnica Esperada

```text
tesis-slm-quechua/
  configs/
    project.yaml
    models.yaml
    rag.yaml
    evaluation.yaml
  data/
    raw/
    cleaned/
    rag_corpus/
    train/
    eval/
    synthetic/
  src/
    common/
      paths.py
      logging.py
      schema.py
    ingest/
      collect_sources.py
      clean_text.py
      chunk_documents.py
      build_manifest.py
    rag/
      bm25_index.py
      vector_index.py
      hybrid_retriever.py
      context_builder.py
    inference/
      model_runner.py
      prompt_templates.py
      language_router.py
    evaluation/
      retrieval_metrics.py
      generation_metrics.py
      technical_metrics.py
      human_rubric.py
    experiments/
      run_experiment.py
      registry.py
  tests/
    test_clean_text.py
    test_chunk_documents.py
    test_language_router.py
    test_hybrid_retriever.py
    test_metrics.py
  experiments/
    E1_base/
    E2_rag/
    E3_rules/
    E4_rag_rules/
    E5_qlora/
    E6_hybrid/
  reports/
```

## Fase 0: Higiene Del Proyecto

**Proposito:** dejar el proyecto seguro antes de implementar.

**Archivos:**

- Modificar: `tesis-slm-quechua/README.md`
- Crear: `tesis-slm-quechua/docs/decisions/0001-alcance-y-hardware.md`
- Crear: `tesis-slm-quechua/configs/project.yaml`

**Pasos:**

- [ ] Confirmar estado de Git y no mezclar cambios de tesis con commits tecnicos.

```powershell
git status -sb
```

Resultado esperado: cualquier cambio en `Plan de Tesis/` se trata como cambio de tesis, no como parte del prototipo.

- [ ] Registrar restricciones de hardware.

Crear `tesis-slm-quechua/docs/decisions/0001-alcance-y-hardware.md`:

```markdown
# Decision 0001: Alcance Y Hardware

El prototipo sera textual y offline.

Hardware observado:
- GPU: NVIDIA GTX 1050 Ti, 4 GB VRAM.
- Sistema local: Windows.
- Python: 3.11 en `tesis-slm-quechua/.venv`.

Implicancias:
- Qwen2.5-3B sera el modelo local por defecto.
- 7B queda como variante de calidad solo si las pruebas de CPU/RAM son aceptables.
- QLoRA es opcional y debe ejecutarse en WSL2, Colab o Kaggle, no como requisito nativo de Windows.
- RAG y evaluacion deben funcionar antes de iniciar QLoRA.
```

- [ ] Crear `tesis-slm-quechua/configs/project.yaml`:

```yaml
project:
  name: tesis-slm-quechua
  language_pair:
    primary: es
    target: qu-collao
  scope:
    grades: ["3", "4", "5", "6"]
    domains: ["comunicacion", "ciencia_y_tecnologia"]
  offline_required: true
  voice_enabled: false

hardware:
  gpu: "NVIDIA GTX 1050 Ti"
  vram_gb: 4
  preferred_base_model: "Qwen2.5-3B-Instruct"
  qlora_native_windows: false
```

**Criterio de avance:**

- Existe un archivo de alcance tecnico.
- El README tecnico apunta a las decisiones y configuraciones.

## Fase 1: Inventario De Datos Y Manifiesto

**Proposito:** saber exactamente que documentos existen antes de indexar o entrenar.

**Archivos:**

- Crear: `tesis-slm-quechua/data/raw/README.md`
- Crear: `tesis-slm-quechua/data/manifest.csv`
- Crear: `tesis-slm-quechua/src/ingest/build_manifest.py`
- Crear prueba: `tesis-slm-quechua/tests/test_manifest.py`

**Regla de datos:** toda fuente debe registrar dialecto, licencia/fuente, tipo documental, grado/dominio y permiso de uso.

Columnas del manifiesto:

```csv
id,path,title,language,dialect,domain,grade,source_type,source_url,license_status,use_in_rag,use_in_train,use_in_eval,notes
```

**Pasos:**

- [ ] Agregar un generador de manifiesto que inspeccione `data/raw/`.
- [ ] Agregar pruebas para columnas obligatorias y archivos faltantes.
- [ ] Registrar recursos iniciales conocidos por la tesis:
  - corpus OCR Collao de Orcotoma et al.;
  - materiales curriculares EIB del MINEDU;
  - glosarios y diccionarios locales;
  - recursos AmericasNLP solo como `non_collao_transfer`, no como Collao.

**Criterio de avance:**

- Existe `data/manifest.csv`.
- Ningun documento entra al RAG sin `dialect` y `use_in_rag`.
- Recursos Chanka, Cusco y Collao no se mezclan silenciosamente.

## Fase 2: Limpieza, Normalizacion Y Fragmentacion

**Proposito:** construir fragmentos limpios, cortos y trazables para RAG.

**Archivos:**

- Crear: `tesis-slm-quechua/configs/rag.yaml`
- Crear: `tesis-slm-quechua/src/ingest/clean_text.py`
- Crear: `tesis-slm-quechua/src/ingest/chunk_documents.py`
- Crear: `tesis-slm-quechua/data/rag_corpus/chunks.jsonl`
- Crear prueba: `tesis-slm-quechua/tests/test_clean_text.py`
- Crear prueba: `tesis-slm-quechua/tests/test_chunk_documents.py`

Configuracion base:

```yaml
chunking:
  prose_tokens_min: 250
  prose_tokens_max: 400
  overlap_tokens: 60
  glossary_mode: one_entry_per_chunk
retrieval:
  final_top_k: 5
  dense_top_k: 20
  bm25_top_k: 20
```

Esquema de chunk:

```json
{
  "chunk_id": "doc001_0001",
  "source_id": "doc001",
  "text": "...",
  "language": "es|qu|mixed",
  "dialect": "collao|chanka|cusco|unknown",
  "domain": "comunicacion|ciencia_y_tecnologia|glossary",
  "grade": "3|4|5|6|na",
  "source_ref": "page/section",
  "tokens_estimated": 312
}
```

**Criterio de avance:**

- Los chunks conservan referencia a la fuente.
- Los chunks de prosa no superan 400 tokens estimados.
- Los glosarios se indexan como una entrada por chunk.
- Todo dato mixto o no Collao queda etiquetado.

## Fase 3: Evaluacion Antes Del Modelo

**Proposito:** evitar construir el sistema sin una meta de prueba fija.

**Archivos:**

- Crear: `tesis-slm-quechua/data/eval/questions_seed.csv`
- Crear: `tesis-slm-quechua/data/eval/rubric.md`
- Crear: `tesis-slm-quechua/configs/evaluation.yaml`

Columnas del banco de preguntas:

```csv
id,question,language,dialect,domain,grade,expected_source_id,reference_answer_es,reference_answer_qu,evaluation_type
```

Minimo antes de implementar E1/E2:

- 10 preguntas en espanol.
- 10 preguntas en Quechua Collao.
- 10 preguntas mixtas con alternancia de codigo.
- Incluir vocabulario, explicacion curricular y retroalimentacion pedagogica.

**Criterio de avance:**

- Existen al menos 30 preguntas semilla.
- Cada pregunta tiene fuente esperada o queda marcada como general.
- La rubrica cubre factualidad, idioma, dialecto, pedagogia y seguridad.

## Fase 4: Deteccion De Idioma Y Reglas De Prompt

**Proposito:** enrutar consultas en espanol, Quechua Collao y mixtas antes de recuperar o generar.

**Archivos:**

- Crear: `tesis-slm-quechua/src/inference/language_router.py`
- Crear: `tesis-slm-quechua/src/inference/prompt_templates.py`
- Crear prueba: `tesis-slm-quechua/tests/test_language_router.py`

Etiquetas del router:

```text
es
qu_collao
mixed_es_qu
unknown
```

**Criterio de avance:**

- El router maneja entradas cortas.
- El router no afirma certeza dialectal cuando la evidencia es debil.
- Las entradas mixtas se aceptan y usan plantillas bilingues.

## Fase 5: RAG Hibrido Base

**Proposito:** implementar RAG antes de cualquier fine-tuning.

**Archivos:**

- Crear: `tesis-slm-quechua/src/rag/bm25_index.py`
- Crear: `tesis-slm-quechua/src/rag/vector_index.py`
- Crear: `tesis-slm-quechua/src/rag/hybrid_retriever.py`
- Crear: `tesis-slm-quechua/src/rag/context_builder.py`
- Crear prueba: `tesis-slm-quechua/tests/test_hybrid_retriever.py`

Comportamiento esperado:

- BM25 captura terminos exactos de glosario.
- Recuperacion densa captura coincidencias semanticas curriculares.
- El contexto final queda limitado a 3-5 chunks.
- El contexto incluye IDs de fuente para trazabilidad.

**Criterio de avance:**

- Se puede calcular Recall@5 sobre el banco de evaluacion.
- Los chunks recuperados son auditables por `source_id`.
- El prompt no excede el presupuesto de contexto configurado.

## Fase 6: Ejecutor Local Del Modelo

**Proposito:** ejecutar el modelo local mediante una interfaz unica.

**Archivos:**

- Crear: `tesis-slm-quechua/configs/models.yaml`
- Crear: `tesis-slm-quechua/src/inference/model_runner.py`
- Crear: `tesis-slm-quechua/src/experiments/run_experiment.py`

Backends en orden de prioridad:

1. Ollama para pruebas rapidas.
2. llama.cpp/GGUF para reproducibilidad offline final.
3. Transformers solo para diagnosticos pequenos.

**Criterio de avance:**

- E1 responde las 30 preguntas semilla sin RAG.
- Se registran latencia, tokens/s cuando sea posible y errores.
- El ejecutor funciona sin internet cuando el modelo ya esta local.

## Fase 7: Experimentos E1-E4

**Proposito:** generar la primera evidencia de tesis sin QLoRA.

**Archivos:**

- Crear: `tesis-slm-quechua/experiments/E1_base/run.yaml`
- Crear: `tesis-slm-quechua/experiments/E2_rag/run.yaml`
- Crear: `tesis-slm-quechua/experiments/E3_rules/run.yaml`
- Crear: `tesis-slm-quechua/experiments/E4_rag_rules/run.yaml`
- Crear: `tesis-slm-quechua/reports/E1_E4_summary.md`

Configuraciones:

- E1: solo modelo.
- E2: modelo + RAG.
- E3: modelo + reglas linguisticas/pedagogicas, sin RAG.
- E4: modelo + RAG + reglas.

Metricas:

- Tecnicas: latencia, RAM, tokens/s, tasa de fallos.
- Recuperacion: Recall@k, MRR, nDCG.
- Generacion: RAGAS cuando aplique, BERTScore/SacreBLEU/chrF++ cuando existan referencias.
- Validacion humana: exportacion lista para rubrica EIB.

**Criterio de avance:**

- E1-E4 usan el mismo banco de preguntas.
- Las salidas se guardan como JSONL con prompt, IDs de contexto, respuesta, metricas y timestamp.
- El resumen indica si RAG mejora o perjudica las respuestas.

## Fase 8: Puerta De Factibilidad QLoRA

**Proposito:** decidir si E5/E6 valen la pena.

**Archivos:**

- Crear: `tesis-slm-quechua/reports/qlora_feasibility.md`
- Crear: `tesis-slm-quechua/configs/qlora.yaml`
- Crear: `tesis-slm-quechua/data/train/README.md`

Condiciones para avanzar:

- Existen al menos 100 ejemplos supervisados de calidad.
- Los datos de entrenamiento son disjuntos de evaluacion y del indice RAG.
- Hay ruta disponible en WSL2, Colab o Kaggle.
- E4 ya fue medido.

**Criterio de avance:**

- Si la puerta falla, QLoRA se documenta como trabajo futuro y no se fuerza E5/E6.
- Si la puerta pasa, se entrena solo un adaptador rank 8 o 16.

## Fase 9: Experimentos E5-E6 Opcionales

**Proposito:** probar si QLoRA mejora estilo, terminologia y uso del contexto.

**Archivos:**

- Crear: `tesis-slm-quechua/src/finetune/prepare_qlora_dataset.py`
- Crear: `tesis-slm-quechua/src/finetune/train_qlora.py`
- Crear: `tesis-slm-quechua/experiments/E5_qlora/run.yaml`
- Crear: `tesis-slm-quechua/experiments/E6_hybrid/run.yaml`

Regla de entrenamiento:

QLoRA no debe usarse para memorizar conocimiento factual curricular. Su objetivo es:

- formato de respuesta;
- andamiaje pedagogico;
- consistencia terminologica;
- uso del contexto RAG en lugar de ignorarlo.

**Criterio de avance:**

- El adaptador se guarda en `models/adapters/`, pero no se commitea si es pesado.
- E5/E6 usan el mismo banco de evaluacion que E1-E4.
- El reporte declara si QLoRA es beneficioso, neutro o no justificado.

## Fase 10: Exportacion De Evidencia Para La Tesis

**Proposito:** convertir resultados tecnicos en tablas listas para la tesis.

**Archivos:**

- Crear: `tesis-slm-quechua/reports/thesis_tables.md`
- Crear: `tesis-slm-quechua/reports/thesis_figures.md`
- Opcional modificar: `Plan de Tesis/partes/05bFactibilidad.tex`
- Opcional modificar: `Plan de Tesis/partes/06cierre.tex`

**Criterio de avance:**

- Las tablas corresponden directamente a las metricas de la tesis.
- Cada afirmacion tiene ID de experimento y ruta de salida.
- Ninguna metrica no verificada entra a la tesis.

## Orden Correcto De Ejecucion

1. Fase 0: higiene del proyecto.
2. Fase 1: inventario de datos.
3. Fase 3: banco semilla de evaluacion.
4. Fase 2: limpieza y fragmentacion.
5. Fase 4: router de idioma y reglas.
6. Fase 5: recuperacion hibrida.
7. Fase 6: ejecutor local del modelo.
8. Fase 7: experimentos E1-E4.
9. Fase 8: puerta QLoRA.
10. Fase 9: E5-E6 solo si se justifica.
11. Fase 10: exportacion a tesis.

Este orden es intencional: la evaluacion debe existir antes de optimizar el sistema, y RAG debe medirse antes de QLoRA.

## Proximas Tareas Inmediatas

1. Crear `configs/project.yaml`.
2. Crear `docs/decisions/0001-alcance-y-hardware.md`.
3. Crear el primer `data/manifest.csv`.
4. Crear un banco semilla de 30 preguntas.
5. Implementar pruebas de limpieza y fragmentacion antes de recuperar documentos.

## Riesgos A Controlar

- Los archivos LaTeX muestran problemas de codificacion al verse en consola; preservar encoding antes de editar texto de tesis.
- No mezclar cambios de `Plan de Tesis/` con commits del prototipo.
- No commitear `.venv`, modelos, datasets, adaptadores, GGUF, checkpoints ni datos privados de validacion.
- No construir UI antes de medir E1-E4.
- No iniciar QLoRA antes de la puerta de factibilidad.

## Revision Del Plan

- Cubre objetivos de tesis: si.
- Preserva restriccion offline: si.
- Deja QLoRA como opcional y condicionado: si.
- Separa tesis y prototipo tecnico: si.
- Define criterios medibles de avance: si.
