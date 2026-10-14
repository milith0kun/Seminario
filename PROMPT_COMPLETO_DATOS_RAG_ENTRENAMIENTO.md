# PROMPT MAESTRO INTEGRAL: DATOS, RAG CON EMBEDDINGS, ENTRENAMIENTO QLORA Y EVALUACIÓN DE 3 ESCENARIOS

> **Rol Asignado:** Actúa como Investigador Principal y Científico de Datos Senior experto en NLP para Lenguas Originarias (Quechua Collao), Modelos de Lenguaje Pequeños (*Small Language Models* - SLM), Sistemas RAG Vectoriales (*Retrieval-Augmented Generation*), Entrenamiento Eficiente (QLoRA/PEFT) y Despliegue *On-Device* en Android con Google LiteRT.

---

## 🎯 OBJETIVO GENERAL
Ejecutar el ciclo completo de investigación, ingeniería de datos, pipeline RAG, fine-tuning y evaluación comparativa de la tesis: **"Asistente Pedagógico SLM + RAG para Quechua Collao en Dispositivos Móviles Android"**.

El proyecto debe validar científicamente los siguientes **3 Escenarios Experimentales**:
1. **Escenario E1 (Control Baseline):** `Qwen2.5-3B-Instruct` Base comercial sin contexto curricular (**RAG Desactivado**), para cuantificar alucinaciones y limitaciones morfológicas.
2. **Escenario E2 (SLM Base + RAG Curricular):** `Qwen2.5-3B-Instruct` Base comercial con recuperación vectorial de fragmentos curriculares MINEDU (**RAG Activado mediante Embeddings y Distancia Coseno**).
3. **Escenario E3 (SLM Entrenado + RAG Curricular):** `Qwen2.5-3B` adaptado con matrices QLoRA para Quechua Collao y pedagogía EIB, con recuperación vectorial (**RAG Activado**).

---

## 📂 ESTRUCTURA DEL PROYECTO Y REGLAS DE TRABAJO
* **Documentación y Plan de Tesis:** `Plan de Tesis/` (consultar fuentes bibliográficas, matrices de consistencia y rúbricas).
* **Backend, Datos, Scripts y Modelos:** `tesis-slm-quechua/`
  * `data/raw/`: Documentos curriculares MINEDU originales (PDFs, textos EIB).
  * `data/processed/`: Chunks limpios, vectorizados y pares QA.
  * `data/eval/`: Batería de 100 consultas curriculares doradas.
  * `models/`: Checkpoints, adaptadores LoRA y binarios `.litertlm`.
  * `scripts/`: Scripts de limpieza, embeddings, indexación, entrenamiento y evaluación.
* **Frontend Android:** `repos-externos/gallery/Android/src/` (App Google AI Edge Gallery en Kotlin / Jetpack Compose).

---

## 🛠️ FASE 1: CURACIÓN, LIMPIEZA Y GENERACIÓN DE DATOS VERIFICADOS

1. **Normalización Lingüística Estricta (Quechua Collao):**
   * Aplicar la normativa oficial trivocálica del MINEDU (**RM 1218-85-ED**: uso exclusivo de grafías *a, i, u* y consonantes *ch, chh, ch', k, kh, k', p, ph, p', q, qh, q', t, th, t', h, k, l, ll, m, n, ñ, p, r, s, t, w, y*).
   * Filtrar y eliminar contaminación dialectal no correspondiente a Collao (remover sufijos específicos de Ayacucho-Chanka o Ancash).
2. **Segmentación y Chunking para Base de Conocimiento RAG:**
   * Procesar los manuales y guías curriculares MINEDU de Educación Intercultural Bilingüe (EIB).
   * Generar fragmentos pedagógicos estructurados de **150 a 300 tokens**, preservando el contexto temático, grado escolar (Ciclos III, IV, V de Primaria) y competencia curricular.
3. **Generación Aumentada de Datos de Entrenamiento (QLoRA) y Evaluación:**
   * Construir y enriquecer el dataset de entrenamiento supervisado (`train_eib_quechua.jsonl`) con al menos 1,500 pares pedagógicos (*Instrucción*, *Entrada*, *Respuesta*):
     * Andamiaje bilingüe (explicaciones en Quechua Collao con soporte en Castellano).
     * Morfología aglutinante (sufijación verbal, nominal, validadores y evidenciales: *-pas, -qa, -mi/-m, -chá, -chu, -man, -raq, -ña*).
     * Rutinas docentes y didáctica intercultural.
   * Consolidar el dataset de prueba blindado (`data/eval/100_consultas_minedu.jsonl`) con 100 consultas verificadas con respuesta de referencia dorada (*Gold Truth*).

---

## 🔍 FASE 2: MOTOR RAG VECTORIAL (EMBEDDINGS + DISTANCIA COSENO)

1. **Generación de Embeddings Locales:**
   * Utilizar un modelo de embeddings multilingüe optimizado (ej. `BAAI/bge-small-en-v1.5`, `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` o embeddings LiteRT locales).
   * Generar vectores densos para cada fragmento curricular de la base de conocimiento y guardarlos en un índice vectorial estructurado (`tesis-slm-quechua/data/processed/indice_curricular.faiss` o `.npz` con metadatos JSON).
2. **Pipeline de Recuperación y Búsqueda por Distancia Coseno:**
   * Implementar la función de similitud:
     $$\text{Similitud}(q, d) = \frac{\mathbf{e}_q \cdot \mathbf{e}_d}{\|\mathbf{e}_q\| \|\mathbf{e}_d\|}$$
   * Configurar recuperación *Top-k* ($k=3$), filtrado por umbral de relevancia ($\text{score} \ge 0.65$) y formateo dinámico del contexto inyectado al Prompt del SLM.

---

## ⚡ FASE 3: ENTRENAMIENTO QLORA Y FUSIÓN DE NUEVOS PESOS (.litertlm)

1. **Fine-Tuning con QLoRA (`train_qlora_quechua.py`):**
   * Cargar `Qwen/Qwen2.5-3B-Instruct` en cuantización 4-bit (NF4 con `bitsandbytes`).
   * Configuración LoRA: Rank $r=16$, $\alpha=32$, Dropout $0.05$, módulos objetivo: `["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]`.
   * Entrenar por 3 a 5 épocas controlando pérdida (*loss*) y evaluando en conjunto de validación.
2. **Fusión de Matrices y Conversión a LiteRT:**
   * Fusionar los pesos adaptados con el modelo base original:
     $$W_{\text{final}} = W_{\text{base}} + \frac{\alpha}{r} (A \cdot B)$$
   * Exportar el modelo fusionado a formato **LiteRT `.litertlm`** de 4-bit / 8-bit para ejecución directa en el runtime de C++ en Android.
   * Ubicar el archivo de pesos resultante en `tesis-slm-quechua/models/Qwen2.5-3B-Instruct-QLoRA-Quechua.litertlm` y verificar su tamaño e integridad de bytes.

---

## 📊 FASE 4: EVALUACIÓN FORMAL DE LOS 3 ESCENARIOS

Ejecutar la suite automatizada sobre las 100 consultas curriculares:
```powershell
cd d:\Proyectos\Seminario\tesis-slm-quechua
.\.venv\Scripts\python.exe scripts/evaluar_escenarios.py --escenarios E1,E2,E3 --output results/benchmark_100_eval.json
```

### Métricas Obligatorias a Calcular:
1. **Calidad Lingüística y Morfológica Quechua:**
   * **chrF++:** (Métrica reina para Quechua Collao a nivel de n-gramas de caracteres y palabras).
   * **BLEU-4 y ROUGE-L:** Coincidencia frente a la respuesta dorada docente.
   * **Similitud Coseno Semántica:** Proximidad semántica de la respuesta generada.
2. **Métricas RAGAS (Fundamentación y Reducción de Alucinaciones):**
   * **Faithfulness (Fidelidad):** $\frac{\text{Afirmaciones sustentadas en documentos MINEDU}}{\text{Total de afirmaciones emitidas}}$.
   * **Answer Relevance (Relevancia):** Pertinencia pedagógica ante la consulta del estudiante.
3. **Eficiencia en Hardware Móvil:**
   * **TTFT (Time To First Token en ms):** Tiempo de respuesta inicial.
   * **Throughput (tokens/seg):** Velocidad de generación sostenida.
   * **Uso de RAM Pico (MB) y Huella de Almacenamiento (GB).**

---

## 📱 FASE 5: INTEGRACIÓN Y VERIFICACIÓN EN APP ANDROID

1. **Configuración del Catálogo:**
   * Asegurar que `model_allowlist.json` contenga los escenarios con `minDeviceMemoryInGb: 4`:
     * `Qwen2.5-3B Base (E1 Control - E2 con RAG)`
     * `Qwen2.5-3B Tutor EIB (E3 Entrenado)`
2. **Compilación e Instalación:**
   ```powershell
   $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
   $env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
   $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
   cd d:\Proyectos\Seminario\repos-externos\gallery\Android\src
   .\gradlew.bat assembleDebug
   adb install -r "d:\Proyectos\Seminario\Gallery-app-debug.apk"
   ```
3. **Verificación en Emulador/Dispositivo:**
   * Configurar el emulador con **6 GB de RAM** (`hw.ramSize=6144` en `config.ini`) y verificar que el chat abra e interactúe sin cierres forzados.

---

## 📑 ENTREGABLES FINALES REQUERIDOS
1. Archivo JSON con los resultados detallados de las 100 consultas (`results/benchmark_100_eval.json`).
2. Tabla comparativa consolidada en Markdown / LaTeX con las métricas promedio de **E1 vs E2 vs E3**.
3. Gráficos de barras y radar comparando *chrF++*, *Faithfulness*, *Latencia TTFT* y *Uso de RAM*.
4. APK final funcional probado en el emulador/dispositivo Android.
