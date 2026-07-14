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

## 3. Cómo regenerar el PDF

Desde la carpeta `Plan de Tesis/`, con MiKTeX instalado:

```
pdflatex PlanTesis_SLM_QuechuaCollao.tex
bibtex   PlanTesis_SLM_QuechuaCollao
pdflatex PlanTesis_SLM_QuechuaCollao.tex
pdflatex PlanTesis_SLM_QuechuaCollao.tex
```
