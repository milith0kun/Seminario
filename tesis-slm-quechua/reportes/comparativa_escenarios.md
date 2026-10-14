# Comparativa experimental de escenarios E1 / E2 / E3

Asistente pedagogico SLM + RAG para Quechua Collao en Android.

## 1. Configuracion de la corrida

| Parametro | Valor |
| --- | --- |
| Fecha (UTC) | 2026-08-30T05:52:53.615046+00:00 |
| Modelo de generacion | `qwen2.5-3b-instruct-q4_k_m.gguf` |
| Modelo de embeddings | `multilingual-e5-small` |
| Backend | llama.cpp (CPU) |
| Plataforma | Windows 10 / AMD64 |
| Consultas evaluadas | 100 |
| Recuperacion | coseno, top-k=3, umbral=0.65 |
| Generacion | max_tokens=192, temperatura=0.2 |
| Adaptador QLoRA disponible | **no** |

## 2. Escenarios comparados

| Escenario | Descripcion | RAG | QLoRA |
| --- | --- | --- | --- |
| **E1** | Control zero-shot (sin RAG) | no | no |
| **E2** | SLM base + RAG curricular | si | no |
| **E3** | SLM adaptado + RAG + andamiaje EIB | si | no |

> **Salvedades declaradas por el pipeline**
>
> - **E3**: Adaptador QLoRA no encontrado en modelos/adaptadores/qlora_quechua_collao. E3 se ejecuto sobre el modelo BASE: la diferencia frente a E2 mide el efecto del prompt de andamiaje, NO el del entrenamiento.

## 3. Calidad linguistica y semantica

Calculado sobre las consultas con respaldo curricular (las sondas de alucinacion se excluyen: su respuesta correcta es una abstencion, no un parafraseo).

| Escenario | chrF++ | BLEU-4 | ROUGE-L | Similitud coseno |
| --- | --- | --- | --- | --- |
| **E1** | 15.14 (+0.00) | 1.67 (+0.00) | 11.81 (+0.00) | 0.859 (+0.000) |
| **E2** | 29.04 (+13.90) | 6.53 (+4.86) | 21.41 (+9.59) | 0.889 (+0.030) |
| **E3** | 26.32 (+11.18) | 7.80 (+6.13) | 18.35 (+6.54) | 0.883 (+0.024) |

Los valores entre parentesis son la diferencia frente a **E1** (control).

## 4. Fundamentacion y pertinencia

| Escenario | Faithfulness | Answer relevance | Cobertura de contexto | Items con contexto |
| --- | --- | --- | --- | --- |
| **E1** | 0.000 | 0.895 | 0.000 | 0 |
| **E2** | 0.320 | 0.910 | 0.251 | 93 |
| **E3** | 0.299 | 0.880 | 0.362 | 93 |

> Faithfulness y answer relevance son **aproximaciones locales deterministas**, no los estimadores de la libreria RAGAS: esta requiere un LLM juez por API y el pipeline se mantuvo offline. Faithfulness es 0 por definicion cuando no se inyecta contexto (caso de E1), porque no hay fuente que fundamente la respuesta.

## 5. Alucinacion (sondas sin respaldo curricular)

Consultas cuya respuesta no existe en el corpus. La respuesta correcta es reconocer el desconocimiento; afirmar un codigo de resolucion, una pagina o un porcentaje es necesariamente una invencion.

| Escenario | Abstenciones correctas | Tasa de abstencion | Entidades inventadas en sondas | Invencion global |
| --- | --- | --- | --- | --- |
| **E1** | 5/8 | 62.5 % | 1 | 1.0 % |
| **E2** | 5/8 | 62.5 % | 0 | 0.0 % |
| **E3** | 0/8 | 0.0 % | 1 | 1.0 % |

## 6. Eficiencia

| Escenario | TTFT medio (ms) | Throughput (tok/s) | Latencia total media (ms) | RAM pico (MB) |
| --- | --- | --- | --- | --- |
| **E1** | 206 | 20.82 | 3529 | 4239 |
| **E2** | 8827 | 17.60 | 14366 | 4305 |
| **E3** | 8477 | 17.55 | 19228 | 2541 |

> Medido con llama.cpp (CPU) sobre Windows 10 / AMD64. Estas cifras corresponden al banco de pruebas de escritorio y **no** sustituyen la medicion en dispositivo Android, que debe reportarse por separado.

## 7. chrF++ por tipo de consulta

| Tipo de consulta | E1 | E2 | E3 | n |
| --- | --- | --- | --- | --- |
| `comprension_lectora` | 13.65 | 12.74 | 3.63 | 17 |
| `contextualizacion` | 27.67 | 39.70 | 50.51 | 7 |
| `factual` | 18.85 | 20.30 | 17.80 | 20 |
| `glosario` | 7.15 | 4.75 | 4.95 | 31 |
| `mixta` | 14.42 | 14.75 | 10.20 | 2 |
| `pedagogica` | 22.64 | 26.93 | 24.71 | 15 |

## 8. chrF++ por idioma de la consulta

| Idioma | E1 | E2 | E3 | n |
| --- | --- | --- | --- | --- |
| `es` | 22.10 | 30.13 | 28.20 | 36 |
| `mixed_es_qu` | 9.14 | 6.78 | 8.44 | 23 |
| `qu_collao` | 11.73 | 7.29 | 3.22 | 33 |

## 9. Deriva de idioma en consultas formuladas en Quechua Collao

Fraccion de consultas en `qu_collao` que el modelo respondio efectivamente en quechua, medida por densidad de sufijos aglutinantes. Es la contraparte necesaria de chrF++: una caida de solapamiento puede deberse a que el modelo cambio de lengua, no a que empeorara su contenido.

| Escenario | Consultas en quechua | Respuestas en quechua | Tasa |
| --- | --- | --- | --- |
| **E1** | 33 | 13 | 39.4 % |
| **E2** | 33 | 2 | 6.1 % |
| **E3** | 33 | 1 | 3.0 % |

> **Hallazgo.** La recuperacion curricular hunde la tasa de respuesta en quechua del 39.4 % (E1) al 6.1 % (E2). El contexto inyectado es predominantemente castellano y arrastra al modelo a esa lengua, de modo que la respuesta se aleja de la referencia dorada en quechua. Esto explica por que chrF++ mejora en consultas en castellano y **empeora** en las formuladas en Quechua Collao. Es, ademas, el argumento empirico mas directo a favor de la adaptacion QLoRA: el RAG por si solo no dota al modelo de competencia productiva en la lengua originaria.

## 10. Lectura de los resultados

- **Efecto del RAG (E1 -> E2)**: mejora de 13.90 puntos chrF++.
- **Efecto **del prompt de andamiaje unicamente** (sin QLoRA) (E2 -> E3)**: -2.73 puntos chrF++.
- Un chrF++ menor en E3 no implica peor respuesta: el andamiaje produce respuestas largas y estructuradas en cuatro pasos, mientras la respuesta dorada es una definicion breve. El solapamiento de n-gramas penaliza esa diferencia de formato. Para E3 son mas informativas la fundamentacion, la tasa de abstencion y la valoracion pedagogica humana.

## 11. Limitaciones

- El corpus curricular disponible en el repositorio no incluye los manuales EIB completos del MINEDU; el indice se construyo con el material realmente presente. Cada fragmento declara su procedencia en `origen`.
- El conjunto de evaluacion mezcla semillas verificadas, consultas derivadas del corpus y sondas de alucinacion. El campo `procedencia` de cada item permite recalcular cualquier metrica sobre el subconjunto que se considere admisible.
- Las metricas de eficiencia provienen del banco de escritorio (llama.cpp, CPU), no del dispositivo Android.
- **E3 se ejecuto sin adaptador QLoRA.** La comparacion E2 vs E3 mide el prompt de andamiaje, no el entrenamiento.
