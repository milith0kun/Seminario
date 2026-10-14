# Comparativa experimental on-device — E1 / E2 / E3

Barrido ejecutado **dentro de la aplicacion Android**, sobre el runtime LiteRT que despliega la tesis. Todas las cifras de eficiencia proceden del dispositivo.

## 1. Entorno de ejecucion

| Parametro | Valor |
| --- | --- |
| Dispositivo | Google sdk_gphone64_x86_64 |
| ABI | x86_64 |
| Android | 16 |
| RAM total | 5923 MB |
| Runtime |  |
| Modelo | `Qwen2.5-3B Base (E1 Control - E2 con RAG)` |
| Acelerador | CPU |
| Longitud de contexto | 2048 |
| Consultas | 100 |
| Fragmentos del corpus | 56 |
| Recuperacion | coseno, top-k=3, umbral=0.65 |

## 2. Calidad linguistica y semantica

| Escenario | chrF++ | BLEU-4 | ROUGE-L | Coseno |
| --- | --- | --- | --- | --- |
| **E1** | 17.01 (+0.00) | 2.88 (+0.00) | 11.40 (+0.00) | 0.857 (+0.000) |

Diferencia frente a **E1** entre parentesis. Las sondas de alucinacion se excluyen: su respuesta correcta es una abstencion, no un parafraseo.

## 3. Fundamentacion

| Escenario | Faithfulness | Answer relevance | Cobertura de contexto | Items con contexto |
| --- | --- | --- | --- | --- |
| **E1** | 0.000 | 0.899 | 0.000 | 0 |

> Aproximaciones locales deterministas, no los estimadores de RAGAS (que exigen un LLM juez por API).

## 4. Alucinacion

| Escenario | Abstenciones correctas | Tasa | Entidades inventadas | Invencion global |
| --- | --- | --- | --- | --- |
| **E1** | 4/8 | 50.0 % | 1 | 1.0 % |

## 5. Eficiencia on-device

| Escenario | TTFT medio (ms) | TTFT mediana (ms) | Throughput decode (tok/s) | Latencia total (ms) | RAM PSS pico (MB) |
| --- | --- | --- | --- | --- | --- |
| **E1** | 725 | 644 | 6.88 | 14547 | 3643 |


| Escenario | Throughput efectivo (tok/s) | Items con decode medible | Longitud media (chars) |
| --- | --- | --- | --- |
| **E1** | 5.91 | 100 | 416 |

> Medido por la propia app sobre el runtime LiteRT del dispositivo. El *throughput decode* solo promedia los items cuya ventana posterior al primer token supera los 100 ms; el *efectivo* se calcula extremo a extremo e incluye el prefill. El conteo de tokens es una estimacion por palabras y signos: el runtime no expone el tokenizador a este nivel.

La longitud media de respuesta es un control de sanidad: valores de pocos caracteres indican que el modelo dejo de generar y que la corrida no es valida, aunque el JSON se haya escrito sin errores.

## 6. Coste de la recuperacion

| Escenario | Modo | Similitud maxima media | Latencia de recuperacion (ms) | Consultas sin respaldo |
| --- | --- | --- | --- | --- |
| **E1** | sin_rag | 0.000 | 0.0 | 0 |

## 7. chrF++ por idioma de la consulta

| Idioma | E1 | n |
| --- | --- | --- |
| `es` | 20.17 | 36 |
| `mixed_es_qu` | 7.18 | 23 |
| `qu_collao` | 20.41 | 33 |

## 8. Deriva de idioma

| Escenario | Consultas en quechua | Respuestas en quechua | Tasa |
| --- | --- | --- | --- |
| **E1** | 33 | 11 | 33.3 % |

Fraccion de consultas en Quechua Collao que el modelo respondio efectivamente en quechua, por densidad de sufijos aglutinantes. Una caida de chrF++ puede deberse a un cambio de lengua y no a una perdida de contenido.
