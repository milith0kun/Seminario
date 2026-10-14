# GUÍA TÉCNICA DE TRANSFERENCIA - TESIS SLM + RAG QUECHUA COLLAO

> **Propósito:** Documento de transferencia directa y autosuficiente para que cualquier agente de IA o desarrollador pueda continuar, compilar el frontend Android, ejecutar el entrenamiento QLoRA, evaluar formalmente los 3 escenarios experimentales y generar los resultados de la tesis sin fricción.

---

## 1. Contexto y Objetivos del Proyecto

* **Tema:** Asistente pedagógico inteligente bilingüe (Quechua Collao - Castellano) para Educación Intercultural Bilingüe (EIB) ejecutado localmente *on-device* en Android.
* **Backbone SLM Objetivo:** `Qwen2.5-3B-Instruct` cuantizado en 4-bit / 8-bit desplegado mediante **LiteRT-LM** (Google AI Edge).
* **Restricción de Hardware Local:** PC Windows con GPU GTX 1050 Ti (4 GB VRAM) / Emulador Android Studio / WSL2 Ubuntu para herramientas basadas en Linux y `bitsandbytes`.

---

## 2. Los Tres Escenarios de Evaluación de la Tesis

| Escenario | Nombre | Configuración del Modelo | RAG Curricular | Propósito Científico |
| :--- | :--- | :--- | :--- | :--- |
| **E1** | **Control Zero-Shot Base** | `Qwen2.5-3B-Instruct` original puro | **Apagado** | Medir la capacidad lingüística base del modelo comercial sin soporte contextual ni adaptación. |
| **E2** | **SLM Base + RAG Curricular** | `Qwen2.5-3B-Instruct` original puro | **Encendido** (Documentos MINEDU) | Medir el impacto de la recuperación contextual en reducir alucinaciones y fundamentar respuestas en el currículo EIB. |
| **E3** | **SLM Adaptado (QLoRA) + RAG** | `Qwen2.5-3B` + Matrices QLoRA Quechua fusionadas en `.litertlm` | **Encendido** (Documentos MINEDU) | Medir el beneficio conjunto de la resiliencia morfológica/andamiaje bilingüe entrenado junto con la fundamentación RAG. |

---

## 3. Arquitectura del Frontend Android (`repos-externos/gallery/Android/src`)

El frontend es una personalización avanzada de **Google AI Edge Gallery** basada en Jetpack Compose, Hilt y LiteRT C++ Runtime:

### Componentes Clave:
1. **Catálogo de Modelos (`model_allowlists/1_0_19.json` y `model_allowlist.json`):**
   * Contiene los modelos de la tesis listados al inicio:
     * `Qwen2.5-3B Base (E1 Control - E2 con RAG)`
     * `Qwen2.5-3B Tutor EIB (E3 Entrenado)`
   * Configurados con `minDeviceMemoryInGb: 4` para evitar alertas bloqueantes en emulador.
2. **Navegación Robusta en Jetpack Compose (`GalleryNavGraph.kt`):**
   * Maneja rutas dinámicas con `Uri.encode(model.name)` y `Uri.decode(rawName)` para prevenir crashes por caracteres especiales (`-`, espacios, etc.).
3. **Pipeline RAG Nativo (`LlmChatViewModel.kt`):**
   * Ubicación: `repos-externos/gallery/Android/src/app/src/main/java/com/google/ai/edge/gallery/ui/llmchat/LlmChatViewModel.kt`.
   * Realiza la inyección de fragmentos curriculares recuperados de la base de conocimiento local antes de enviar el prompt a LiteRT.
4. **Requisitos Críticos del Emulador Android:**
   * **RAM:** Configurada en **6 GB (6144 MB)** (`hw.ramSize=6144` en `config.ini`). Si tiene 2 GB, el sistema Android cerrará la app por falta de memoria al inicializar XNNPack.
   * **Almacenamiento:** Mínimo **8 GB libres** en `/data` debido a la compilación de tensores en caché XNNPack (~2.5 GB por modelo).
   * **Archivo de Pesos:** Ubicado en `/storage/emulated/0/Android/data/com.google.aiedge.gallery/files/<Model_Dir>/<hash>/Qwen2.5_Coder_3B_It.litertlm` con tamaño exacto de **3,433,083,824 bytes**.

---

## 4. Pipeline de Entrenamiento y Fusión QLoRA (`tesis-slm-quechua/`)

1. **Datos de Entrenamiento:**
   * Corpus estructurado en `tesis-slm-quechua/data/` (Pares lingüísticos Quechua Collao, diálogos pedagógicos EIB, normas gramaticales normalizadas según RM 1218-85-ED).
2. **Entrenamiento QLoRA:**
   * Script base: `tesis-slm-quechua/scripts/train_qlora_quechua.py`.
   * Hiperparámetros: $r=16$, $\alpha=32$, `target_modules=["q_proj", "k_proj", "v_proj", "o_proj"]`, 4-bit `NF4`, learning rate $2\times 10^{-4}$.
3. **Fusión y Conversión a LiteRT `.litertlm`:**
   * Fusión de adaptadores LoRA sobre los pesos base de HuggingFace.
   * Conversión con `ai-edge-torch` / MediaPipe Model Maker a formato binario `.litertlm` para ejecución directa en CPU/GPU móvil.

---

## 5. Protocolo de Evaluación Experimental (100 Consultas Curriculares)

### Ejecución del Benchmark Automatizado:
* **Script:** `tesis-slm-quechua/scripts/evaluar_escenarios.py`
* **Dataset de Entrada:** `tesis-slm-quechua/data/eval/100_consultas_minedu.jsonl`
* **Ejecución:**
  ```powershell
  cd d:\Proyectos\Seminario\tesis-slm-quechua
  .\.venv\Scripts\python.exe scripts/evaluar_escenarios.py --escenarios E1,E2,E3 --output results/benchmark_100_eval.json
  ```

### Métricas Obligatorias a Registrar:
1. **Calidad Lingüística y Semántica:**
   * **chrF++:** Métrica estándar para lenguas aglutinantes y polisintéticas como el Quechua Collao (captura precisión a nivel de caracteres y n-gramas morfológicos).
   * **BLEU-4 / ROUGE-L:** Puntuación de traslape léxico frente a la respuesta dorada docente.
   * **Similitud Coseno Semántica:** Mediante embeddings bilingües.
2. **Métricas RAGAS (Fundamentación y Alucinación):**
   * **Faithfulness (Fidelidad):** Proporción de afirmaciones verificables en los fragmentos curriculares recuperados.
   * **Answer Relevance (Relevancia):** Pertinencia pedagógica de la respuesta ante la consulta del estudiante.
3. **Eficiencia en Dispositivo Móvil:**
   * **TTFT (Time To First Token):** Latencia inicial en milisegundos.
   * **Throughput:** Velocidad de generación sostenida (tokens por segundo).
   * **Uso de RAM Pico:** Consumo de memoria del proceso en MB.
   * **Huella en Disco:** Espacio del archivo `.litertlm` + caché compilado.

---

## 6. Comandos Operativos Clave para el Agente

```powershell
# 1. Compilar el APK de la app Android
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"
$env:ANDROID_HOME = "$env:LOCALAPPDATA\Android\Sdk"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
cd d:\Proyectos\Seminario\repos-externos\gallery\Android\src
.\gradlew.bat assembleDebug

# 2. Instalar APK en el emulador o dispositivo físico
adb install -r "d:\Proyectos\Seminario\Gallery-app-debug.apk"

# 3. Transferir el modelo íntegro (3.43 GB)
adb push "d:\Proyectos\Seminario\tesis-slm-quechua\models\Qwen2.5_Coder_3B_It.litertlm" "/storage/emulated/0/Android/data/com.google.aiedge.gallery/files/Qwen2_5_3B_Base__E1_Control___E2_con_RAG_/a32e9f082c3fee8adcbe71990eae1eaca3eb0eb9/Qwen2.5_Coder_3B_It.litertlm"

# 4. Ejecutar el benchmark experimental de los 3 escenarios
cd d:\Proyectos\Seminario\tesis-slm-quechua
.\.venv\Scripts\python.exe scripts/evaluar_escenarios.py
```
