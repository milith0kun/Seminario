# Pipeline experimental — Asistente pedagógico SLM + RAG para Quechua Collao

Guía de ejecución de las cinco fases del experimento, desde la curación de
datos hasta el reporte comparativo de los escenarios E1/E2/E3.

Todos los comandos se ejecutan desde `tesis-slm-quechua/` con el intérprete del
entorno virtual: `.\.venv\Scripts\python.exe` (Windows) o `.venv/bin/python`.

---

## Escenarios comparados

| Escenario | Modelo | RAG | Prompt | Propósito |
| --- | --- | --- | --- | --- |
| **E1** | Base | apagado | directo | Control zero-shot: capacidad lingüística y tasa de alucinación sin soporte contextual. |
| **E2** | Base | encendido | fundamentación en fuentes | Efecto de la recuperación curricular sobre la fundamentación. |
| **E3** | Adaptado (QLoRA) | encendido | andamiaje pedagógico EIB | Efecto conjunto de adaptación y recuperación. |

> **Estado de E3.** El adaptador QLoRA solo existe tras ejecutar la Fase 3. Si
> no está presente, `evaluar_escenarios.py` ejecuta E3 sobre el modelo base y
> lo declara explícitamente en el JSON y en el reporte: en ese caso la
> diferencia E2 → E3 mide el efecto del *prompt* de andamiaje, no el del
> entrenamiento.

---

## Fase 1 — Curación y normalización de datos

```powershell
python scripts/fase1_curar_datos.py --max-segmentos 20000
python scripts/fase1_generar_eval.py --total 100
```

**Qué hace**

1. Filtra el corpus monolingüe `llamacha_monolingual_quechua.jsonl` conservando
   solo segmentos en **Quechua Collao**. La discriminación es fonológica: el
   Collao posee aspiradas (`ph, th, chh, kh, qh`) y glotalizadas (`p', t', ch',
   k', q'`) que el Chanka no puede producir. Los segmentos Chanka y Ancash se
   descartan, como exige el criterio dialectal de la tesis.
2. Normaliza a la ortografía oficial trivocálica (RM 1218-85-ED, vocales
   `a/i/u`), preservando préstamos del castellano y tecnicismos curriculares.
3. Extrae los fragmentos curriculares EIB estructurados y los segmenta a
   150–300 tokens.
4. Construye el conjunto de evaluación de 100 consultas.

**Salidas**

| Archivo | Contenido |
| --- | --- |
| `data/processed/corpus_collao.jsonl` | Corpus monolingüe filtrado a Collao |
| `data/processed/corpus_curricular.jsonl` | Fragmentos curriculares segmentados |
| `data/train/pares_pedagogicos.jsonl` | Pares instrucción/respuesta EIB |
| `data/eval/100_consultas_minedu.jsonl` | Conjunto de evaluación |

**Procedencia de los datos.** Cada consulta de evaluación declara su origen en
el campo `procedencia`, de modo que cualquier métrica puede recalcularse sobre
el subconjunto que se considere admisible:

- `semilla_verificada` — preguntas ya revisadas en el repositorio.
- `derivada_curricular` — construidas sobre un fragmento concreto, enlazado en
  `chunk_esperado`.
- `sonda_alucinacion` — consultas **sin** respaldo en el corpus; la respuesta
  correcta es reconocer el desconocimiento. Sirven para cuantificar alucinación.

Ningún ítem se atribuye a un documento MINEDU ausente del repositorio.

---

## Fase 2 — Motor RAG vectorial

```powershell
python scripts/fase2_construir_indice.py --probar
```

Codifica los fragmentos con `multilingual-e5-small` y persiste el índice.
La recuperación usa similitud de coseno sobre vectores normalizados:

```
sim(q, d) = (e_q · e_d) / (‖e_q‖ ‖e_d‖)
```

### Guardarraíl de cobertura léxica

El umbral de coseno **por sí solo no detecta consultas sin respaldo**. Medido
sobre las 100 consultas de evaluación:

| Conjunto | mín. | mediana | máx. |
| --- | --- | --- | --- |
| Con respaldo curricular | 0.821 | 0.865 | 0.919 |
| Sondas sin respaldo | 0.837 | 0.846 | 0.870 |

Las distribuciones se solapan: ningún corte absoluto las separa, porque e5 es
anisotrópico y comprime las similitudes en una banda alta y estrecha. Con el
umbral 0.65 del plan original, el 100 % de las sondas recuperaba contexto.

La **cobertura léxica** —fracción de términos de contenido de la consulta
presentes en el vocabulario del corpus— sí discrimina, porque las consultas sin
respaldo piden entidades ausentes (códigos de resolución, páginas, porcentajes):
mediana 0.667 con respaldo frente a 0.222 en las sondas. El corte **0.30**
maximiza el índice de Youden (J = 0.875): conserva el 100 % de las consultas
válidas y descarta el 87.5 % de las sondas.

BM25 se descartó como discriminante: puntúa **más alto** en las sondas
(30.1 frente a 19.9), porque estas acumulan términos genéricos frecuentes.

---

## Fase 3 — Adaptación QLoRA

```powershell
python scripts/fase3_construir_dataset_qlora.py
python scripts/train_qlora_quechua.py --epocas 1
python scripts/fase3_fusionar_y_exportar.py --gguf
```

**Dataset de entrenamiento.** Combina tres tareas derivadas de material real:

| Tarea | Función |
| --- | --- |
| `modelado_lengua` | Continuación de texto Collao — adapta morfología y léxico |
| `normalizacion` | Reescritura a ortografía trivocálica oficial |
| `instruccion_eib` | Pares pedagógicos con andamiaje bilingüe |

**Hiperparámetros:** 4-bit NF4 con doble cuantización, `r=16`, `alpha=32`,
`dropout=0.05`, `target_modules = q/k/v/o/gate/up/down_proj`, lr `2e-4`,
scheduler coseno, `paged_adamw_8bit`.

**Requisitos.** El entrenamiento en 4-bit exige CUDA y `bitsandbytes`. La
conversión a `.litertlm` requiere `ai-edge-torch`, que solo publica ruedas para
Linux; `fase3_fusionar_y_exportar.py` detecta la plataforma y emite las
instrucciones para WSL2 en lugar de fallar de forma opaca.

---

## Fase 4 — Benchmark comparativo

El experimento tiene **dos bancos**, y la tesis reporta el segundo:

| Banco | Dónde corre | Para qué sirve |
| --- | --- | --- |
| Escritorio | llama.cpp sobre CPU x86 | Iterar rápido sobre prompts y métricas |
| **On-device** | **LiteRT dentro de la app Android** | **Cifras de la tesis** |

Las latencias de un x86 con llama.cpp no representan el despliegue móvil que
evalúa el trabajo: el TTFT, el throughput y la RAM deben medirse en el
dispositivo.

### 4a. Banco on-device (el que produce los resultados)

```powershell
# 1. Exportar corpus y consultas como assets del APK (vectores precomputados)
python scripts/fase2_exportar_assets_android.py

# 2. Compilar e instalar
cd ../../repos-externos/gallery/Android/src
./gradlew.bat assembleDebug
adb install -r app/build/outputs/apk/debug/app-debug.apk

# 3. Abrir la pantalla de evaluación (deep link, sin depender de la UI)
adb shell am start -a android.intent.action.VIEW `
  -d 'com.google.ai.edge.gallery://evaluacion/Qwen2.5-3B%20Base%20(E1%20Control%20-%20E2%20con%20RAG)'

# 4. Pulsar "Iniciar barrido" y esperar. Al terminar, extraer el JSON:
adb pull /storage/emulated/0/Android/data/com.google.aiedge.gallery/files/benchmark_ondevice.json `
  tesis-slm-quechua/results/

# 5. Calcular métricas
cd ../../../../tesis-slm-quechua
python scripts/fase4_metricas_ondevice.py
```

**Regímenes de recuperación.** El encoder de embeddings no viaja en el APK: los
vectores del corpus y de las 100 consultas se precomputan y se embarcan como
assets, de modo que el barrido usa **coseno real** on-device. Las consultas
libres que escribe el usuario no tienen vector y caen a recuperación léxica
sobre el mismo corpus. Cada medición registra cuál de los dos regímenes usó en
el campo `modoRecuperacion`.

**Longitud de contexto.** `ConfigKeys.MAX_TOKENS` alimenta `maxNumTokens` de la
`EngineConfig` de LiteRT, que es la ventana **total** (prefill + decode), no un
tope de salida. Los prompts de E2/E3 rondan los 1200 tokens con el material
inyectado: por debajo de eso la inferencia falla con *"Input token ids are too
long"*. El valor por defecto (2048) deja margen suficiente y es idéntico en los
tres escenarios.

**Reinicio de sesión por consulta.** El runner llama a `resetSession` antes de
cada consulta. Sin ese reinicio las 100 consultas se acumulan en una sola
conversación: al saturar la ventana de contexto el modelo deja de generar y las
respuestas salen vacías. Medido en la primera corrida — degradación desde la
consulta ~30 y vacío total desde la 40:

| Bloque | Respuestas vacías (sin reinicio) | Con reinicio |
| --- | --- | --- |
| 0–29 | 0 / 30 | 0 / 30 |
| 30–39 | 5 / 10 | 0 / 10 |
| 40–99 | 60 / 60 | 0 / 60 |

Un barrido sin este reinicio produce métricas que parecen válidas —el JSON se
escribe, no hay errores— pero mide sobre respuestas vacías. Conviene verificar
la longitud media de respuesta por bloques antes de dar por buena una corrida.

**Throughput.** `throughputTokS` mide la ventana posterior al primer token y
solo se reporta cuando esa ventana supera los 100 ms; si el runtime entrega la
respuesta de una vez, el cociente se dispara (se llegaron a registrar
997 tok/s). En ese caso vale 0 y queda `throughputEfectivoTokS`, calculado
extremo a extremo, como cifra utilizable. El conteo de tokens es una estimación
por palabras y signos: el runtime no expone el tokenizador a este nivel.

**Liberación entre escenarios.** Cada escenario necesita su propia instrucción
de sistema, que se fija al inicializar el motor. Reinicializar sin llamar antes
a `cleanUp` carga una segunda instancia del modelo de 3,4 GB sobre la anterior
y el proceso muere con SIGSEGV al terminar el primer escenario.

### 4b. Banco de escritorio (iteración)

```powershell
python scripts/evaluar_escenarios.py --escenarios E1,E2,E3 `
    --output results/benchmark_100_eval.json
```

Opciones útiles: `--limite N` para pruebas rápidas, `--max-tokens N` para
ajustar el presupuesto de generación.

La corrida guarda un **checkpoint cada 10 consultas**, de modo que una
interrupción no obliga a repetir el escenario completo.

### Métricas

| Bloque | Métricas |
| --- | --- |
| Lingüístico | chrF++ (principal para lenguas aglutinantes), BLEU-4, ROUGE-L, similitud coseno |
| Fundamentación | Faithfulness, answer relevance, cobertura de contexto |
| Alucinación | Tasa de abstención correcta, entidades inventadas |
| Eficiencia | TTFT, throughput, latencia total, RAM pico |

> **Faithfulness y answer relevance son aproximaciones locales deterministas**,
> no los estimadores de la librería RAGAS: esta requiere un LLM juez accesible
> por API y el pipeline se mantuvo offline y reproducible. Los valores no son
> intercambiables con los de RAGAS y deben reportarse como tales.

---

## Fase 5 — Reporte y verificación en Android

```powershell
python scripts/fase5_generar_reporte.py
powershell -File scripts/aprovisionar_emulador.ps1
```

### Requisitos del emulador

| Recurso | Valor | Motivo |
| --- | --- | --- |
| RAM | 6 GB (`hw.ramSize=6144`) | Con 2 GB el Low Memory Killer cierra la app al inicializar XNNPack |
| Almacenamiento | ≥ 8 GB libres | La caché XNNPack consume ~2.9 GB por modelo, medido |

El emulador **solo aplica un aumento de `disk.dataPartition.size` al arrancar
con `-wipe-data`**; sin ese paso la partición conserva su tamaño anterior.
`aprovisionar_emulador.ps1` automatiza el ciclo completo: reinicio limpio,
instalación del APK, transferencia del catálogo y de los pesos, y verificación
del tamaño exacto del binario (3 433 083 824 bytes).

### Selección de escenario en la app

El escenario lo determina **exclusivamente** el selector *Escenario de
Evaluación Tesis* en el panel de configuración del modelo. No se infiere del
nombre del modelo: los rótulos del catálogo contienen las subcadenas `E1`, `E2`
y `E3` (por ejemplo `Qwen2.5-3B Base (E1 Control - E2 con RAG)`), de modo que
una coincidencia por nombre activaría el RAG siempre e impediría medir E1 como
control.

El switch *Activar RAG Quechua Collao* es un override de ablación y debe
permanecer apagado para que E1 conserve su validez.

---

## Pruebas

```powershell
python -m pytest pruebas/test_pipeline_tesis.py -q
```

Cubren la detección dialectal, la normalización ortográfica, las métricas y el
guardarraíl de recuperación.
