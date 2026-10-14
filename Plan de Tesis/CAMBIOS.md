# Registro de Cambios — Plan de Tesis

Documento de control de las modificaciones realizadas al plan de tesis
*"Diseño y evaluación de un asistente educativo offline español–Quechua Collao…"*.
Todos los cambios fueron **aditivos o de reubicación**: no se eliminó ninguna idea del contenido original.

> Fecha de la sesión de revisión: 2026-07-14
> Herramienta de compilación instalada: MiKTeX 25.12 (no había compilador LaTeX previo).
> Estado del PDF tras los cambios: compila sin errores, sin citas ni referencias sin resolver.

---

## 1. Cambios aplicados

### 1.1 Marco Teórico — `partes/05MarcoTeorico.tex`
| # | Cambio | Motivo |
|---|--------|--------|
| 1 | **Párrafo introductorio** de contextualización al inicio | La guía docente exige una introducción antes de desglosar conceptos |
| 2 | Nueva subsección de cierre **"Síntesis integradora del marco teórico"** (puente a la metodología) | La guía marca como *error crítico* terminar el marco sin conectar con la metodología |
| 3 | Cita `(Vaswani et al., 2017)` en texto plano → `\citep{Vaswani2017}` | Toda definición debe tener cita formal que enlace a la bibliografía |
| 4 | Cita `(Google, 2024)` en tabla de modelos → `\citep{gemma2024}` | Íd. |
| 5 | Cita del **translengüaje** → `\citep{Garcia2009}` | Concepto sin respaldo académico |
| 6 | Cita de la **ZDP** → `\citet{Vygotsky1978}` | Concepto sin respaldo académico |
| 7 | Cita del modelo base **Qwen2.5** → `\citep{qwen2024}` | La entrada existía en el `.bib` pero no se citaba |
| 8 | **Se quitó** la subsección "Antecedentes de la investigación" (tabla-matriz) | Los antecedentes no van en el Marco Teórico; se movió al Estado del Arte |

### 1.2 Estado del Arte — `partes/05EstadoDelArte.tex`
| # | Cambio | Motivo |
|---|--------|--------|
| 9 | **Recibió** la tabla-matriz de antecedentes en nueva subsección "Matriz resumida de antecedentes" (antes de la síntesis crítica) | Consolidar todos los antecedentes en un solo lugar y eliminar la redundancia con el Marco Teórico |
| 10 | Separador decimal `1.5 a 17.6` → `1,5 a 17,6` en la tabla | Coherencia con el resto del documento (coma decimal) |

### 1.3 Estudio de Factibilidad — `partes/05bFactibilidad.tex`
| # | Cambio | Motivo |
|---|--------|--------|
| 11 | Cita `Ovadia et al.` texto plano → `\citet{Ovadia2024}` | Cita formal que enlace |
| 12 | Cita `Dhawan et al. (2026)` texto plano → `\citet{Dhawan2026}` | Íd. |
| 13 | **Frase puente** que explica que los 7 experimentos (E1–E7) descomponen las 3 configuraciones básicas | Evitar que se lea como contradicción "3 vs 7" |
| 14 | Nueva subsección **"Factibilidad legal y de licencias"** | Faltaba tratar los derechos de uso de materiales MINEDU/AMLQ |
| 15 | Nueva fila **"Legal / licencias" (VERDE)** en el semáforo de riesgo | Reflejar la nueva dimensión en el resumen de riesgos |

### 1.4 Carátula — `partes/01caratula.tex`
| # | Cambio | Motivo |
|---|--------|--------|
| 16 | **Título ampliado** a 3 pilares: se añadió *"y recursos lingüísticos validados"* | El título nombraba solo 2 pilares (SLM + RAG) pero el cuerpo describe 3; ahora coincide con Problema general y Resumen |

### 1.5 Aspectos Generales — `partes/04AspectosGenerales.tex`
| # | Cambio | Motivo |
|---|--------|--------|
| 17 | **Objetivo General** alineado con el título (se añadió *"y recursos lingüísticos validados"*) | Coherencia interna del alcance |

### 1.6 Bibliografía — `partes/Bibliografia.bib`
| # | Cambio | Motivo |
|---|--------|--------|
| 18 | Nueva entrada `@book{Garcia2009}` — García, O. (2009). *Bilingual Education in the 21st Century.* Wiley-Blackwell | Respaldo del concepto de translengüaje |
| 19 | Nueva entrada `@book{Vygotsky1978}` — Vygotsky, L. S. (1978). *Mind in Society.* Harvard University Press | Respaldo de la ZDP |

---

## 2. Hallazgos pendientes (requieren tu decisión o verificación)

Estos **no se modificaron** porque implican inventar datos o decisiones que te corresponden a ti / tu asesora.

1. **⚠️ Posible error numérico en la Ficha 5 (Hevia) — `partes/08Anexos.tex`, línea 88.**
   El texto dice *"disminuyó su precisión … de 21.59% a 21.81%"*, pero 21.59 → 21.81 es un **aumento**, no una disminución.
   **Acción sugerida:** verificar los números reales contra el paper de Hevia et al. (2025) y corregir la cifra o la redacción. **No se corrigió para no inventar datos.**

2. **Título / cambio de alcance:** el título se amplió a 3 pilares. **Conviene confirmarlo con la asesora (Ing. Gabriela Zúñiga)** antes de darlo por definitivo. Revertirlo es 1 línea.

3. **Rótulo del modelo base (7B vs 3B):** el Marco Teórico llama a Qwen2.5-7B *"candidato principal"*, mientras la Factibilidad adopta el 3B como *"configuración base"* y el 7B como *"variante de calidad"*. No es contradicción dura, pero conviene unificar el rótulo.

4. **Separador decimal mixto en todo el documento:** conviven la coma (3,4; 17,6) y el punto (6.59; 20.13; 21.59). Se unificó el caso más visible; queda pendiente decidir una convención única (coma o punto) y aplicarla de forma global.

5. **Entradas del `.bib` definidas pero sin citar:** `minedu2016`, `ollama`, `huggingface`, `sbs2026`. No son errores (no se imprimen si no se citan), pero podrían aprovecharse o eliminarse.

---

## 3. Sesión de Reestructuración y Limpieza Metodológica (Octubre 2026)

Se realizó una depuración estructural completa del Plan de Tesis para enfocar el proyecto 100\% en **Ingeniería Informática y de Sistemas (IA / PLN / SLMs y RAG)**, eliminando dependencias de psicología educativa y docentes:

1. **Eliminación de Coautoría:**
   - Se removió formalmente a *Br. Haider Alex Carpio Hermoza* de todas las carátulas y metadatos (`Plan de Tesis/partes/01caratula.tex`, `Review del Plan de Tesis/partes/01caratula_resumen.tex`, `Plan de Tesis - Estructura/partes/01caratula.tex` y `diapositiva/index.html`).
   - El tesista único es **Br. Edmil Jampier Saire Bustamante**.

2. **Respaldo de Componentes Pedagógicos:**
   - Se creó el archivo de archivo [`respaldo_componentes_pedagogicos_eib.md`](file:///d:/Proyectos/Seminario/Plan%20de%20Tesis/respaldo_componentes_pedagogicos_eib.md) con todo el texto original sobre andamiaje cognitivo, fuentes MINEDU de primaria y rúbricas docentes antes de su depuración.

3. **Reorientación del Título y Ámbito (Fórmula Huillca):**
   - **Nuevo Título (15 palabras):**
     *«Diseño e implementación de una arquitectura SLM--RAG con QLoRA para la generación contextualizada en Quechua Collao»*.
   - Se eliminaron los términos *"asistente educativo"*, *"Educación Intercultural Bilingüe (EIB)"* y *"recursos lingüísticos validados"*, adoptando la sigla técnica canónica *QLoRA*.

4. **Reestructuración de Aspectos Generales (`04AspectosGenerales.tex`):**
   - Reducción de 5 subproblemas y 6 objetivos dispersos a **3 problemas específicos y 3 objetivos específicos** basados en las fases cronológicas de ingeniería DSR (Datos $\rightarrow$ Núcleo Técnico/Adaptación $\rightarrow$ Evaluación Computacional).
   - Árboles de problemas y objetivos en TikZ regenerados con 3 nodos técnicos alineados a los ODS 9 y 10.
   - Matriz de consistencia actualizada con correspondencia 1:1 estricta.

5. **Operacionalización de Variables (`InformeVariables.tex` y `05MarcoTeorico.tex`):**
   - Eliminación total de variables cualitativas de andamiaje escolar (VD7) y pertinencia curricular docente (VD8).
   - Incorporación de métricas computacionales puras: Rendimiento (Latencia, Tokens/s, RAM/VRAM), Calidad PLN (chrF++, SacreBLEU, Perplejidad $PPL$), y Fidelidad RAG (Métricas RAGAS: *Faithfulness*, *Context Precision*, *Answer Relevancy*).
   - Sección teórica sobre mecanismos de atención ($W_q, W_k, W_v, W_o$) y formulación matemática de QLoRA ($W = W_0 + \frac{\alpha}{r}BA$) para la utilización de contexto.

6. **Depuración de Factibilidad y Cronograma (`05bFactibilidad.tex`, `06cierre.tex`, `08Anexos.tex`):**
   - Se eliminaron menciones a visitas a colegios, validaciones con docentes EIB y dependencias burocráticas con UGELs.
   - Factibilidad operativa elevada a VERDE por tratarse de un pipeline autónomo y reproducible.
   - Agregada entrada bibliográfica formal `@inproceedings{Hu2021}` para LoRA.

7. **Compilación y Depuración Previa:**
   - Compilación MiKTeX (`pdflatex` + `bibtex`): 44 páginas, 0 errores.

8. **Alineación con la Cátedra del Msc. Raúl Huillca Huallparimachi (Seminario II):**
   - **Carátula (`01caratula.tex`):** Se formalizó la carátula de acuerdo al curso de cátedra, figurando exclusivamente el **Docente:** Msc. Raúl Huillca Huallparimachi (curso **Seminario de Investigación II**) y el tesista **Br. Edmil Jampier Saire Bustamante**, eliminando cualquier mención a asesora externa.
   - **Reestructuración Canónica de Capítulos (`04AspectosGenerales.tex` y `06cierre.tex`):** Se reorganizó el documento en 6 capítulos normalizados acorde a la plantilla oficial de la Escuela Profesional de Ingeniería Informática y de Sistemas (UNSAAC):
     * *Capítulo 1:* Aspectos Generales de la Investigación (Problema $\rightarrow$ Objetivos $\rightarrow$ Hipótesis $\rightarrow$ Justificación $\rightarrow$ Alcances y Limitaciones $\rightarrow$ Matriz de Consistencia).
     * *Capítulo 2:* Estado del Arte.
     * *Capítulo 3:* Marco Teórico y Conceptual.
     * *Capítulo 4:* Metodología (DSR).
     * *Capítulo 5:* Estudio de Factibilidad.
     * *Capítulo 6:* Aspectos Administrativos (Viabilidad, Cronograma y Estructura Capitular).
   - **Índice de Figuras (`03indices.tex`):** Se activó formalmente `\listoffigures` para indexar los árboles TikZ, diagramas de arquitectura y cronograma de Gantt.
   - **Depuración de Anexos (`08Anexos.tex`):** Corrección léxica final en fichas de análisis (eliminación de remanentes de *asistente* y *estudiantes*).

9. **Compilación del PDF Final:**
   - Compilación exitosa con MiKTeX (`pdflatex` + `bibtex`): **45 páginas**, código de salida 0, 0 errores, índices completos.

10. **Reestructuración y Depuración Integral de Gráficas Vectoriales TikZ:**
    - **Figura 1: Árbol de Problemas (`04AspectosGenerales.tex`):** Rediseñado de 4 ramas asimétricas a la tríada estricta de ingeniería DSR (3 Causas Raíz y 3 Efectos Directos) con correspondencia 1:1 respecto a los Problemas Específicos PE1 (Datos y Recuperación), PE2 (Núcleo Técnico y Adaptación) y PE3 (Evaluación Computacional).
    - **Figura 2: Árbol de Objetivos (`04AspectosGenerales.tex`):** Perfeccionamiento de rótulos técnicos para alinear simétricamente los Medios de ingeniería (OE1, OE2, OE3) y los Fines ODS (ODS 9 y ODS 10) con el título oficial de 15 palabras.
    - **Figura 4: Esquema QLoRA (`05MarcoTeorico.tex`):** Corrección del alineamiento geométrico horizontal de los nodos de bajo rango ($A, B$), operador de suma directa ($\oplus$) y vector de salida $h$, eliminando el retroceso visual de flechas hacia la izquierda.
    - **Figura 5: Pipeline RAG Local Offline (`05MarcoTeorico.tex`):** Reestructuración en dos fases claramente rotuladas: *Indexación Documental Offline* (Corpus $\rightarrow$ Segmentación morfológica $\rightarrow$ Embeddings $\rightarrow$ Base vectorial) e *Inferencia Local Online* (Consulta $\rightarrow$ Recuperación densa $\rightarrow$ Inyección en Prompt Aumentado $\rightarrow$ SLM cuantizado con QLoRA $\rightarrow$ Salida en Quechua Collao), eliminando conexiones diagonales erráticas y términos desactualizados.
    - **Figura 7: Arquitectura de Software Modular (`05bFactibilidad.tex`):** Organización en capas de arquitectura de software (Capa de Aplicación/CLI $\rightarrow$ Orquestador Central Python $\rightarrow$ Módulos RAG/Base Vectorial embebida $\rightarrow$ Motor de inferencia C++ `llama.cpp` + GGUF 4 bits + QLoRA).
    - **Figura 8: Pipeline del Diseño Experimental (`05bFactibilidad.tex`):** Eliminación total del cruce y superposición de líneas en la fila de tratamientos; ahora el Banco de 100 Consultas se bifurca en un tridente superior limpio hacia los 3 tratamientos en paralelo (E1: SLM Base, E2: SLM + RAG, E3: SLM + RAG + QLoRA), los cuales convergen ordenadamente hacia la batería de métricas automáticas, inferencia estadística no paramétrica y reporte comparativo.
    - **Figura 9: Diagrama de Gantt y Cronograma (`06cierre.tex`):** Corrección del texto en la barra del mes 4 y tabla administrativa para remover la palabra residual *"en matrices"* por *"Entrenamiento y ajuste de adaptadores QLoRA (PEFT)"*.

---

## 4. Cómo regenerar el PDF

Desde la carpeta `Plan de Tesis/`, con MiKTeX instalado:

```bash
pdflatex -interaction=nonstopmode PlanTesis_SLM_QuechuaCollao.tex
bibtex   PlanTesis_SLM_QuechuaCollao
pdflatex -interaction=nonstopmode PlanTesis_SLM_QuechuaCollao.tex
pdflatex -interaction=nonstopmode PlanTesis_SLM_QuechuaCollao.tex
```
