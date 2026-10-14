# Aplicación del seminario al plan de tesis

Esta carpeta contiene el trabajo de extracción del archivo main.pdf y la aplicación del proceso de seis bloques a la introducción del plan SLM–RAG para Quechua Collao.

## Archivos

- extraccion_37_diapositivas.md: texto legible por diapositiva y descripción visual de las 37 páginas, con un enlace a la imagen de cada una.
- seminario_extraido.txt: salida de extracción textual del PDF, conservada como referencia primaria.
- diapositivas/: 37 imágenes PNG de las páginas del PDF, numeradas del 01 al 37.
- aplicacion_intro_plan_tesis.tex: presentación Beamer de 11 diapositivas, con el proceso de seis bloques aplicado al plan y el estilo de las carpetas de Título y Objetivos.
- aplicacion_intro_plan_tesis.pdf: PDF de la presentación aplicada.
- introduccion_plan_tesis_fragmento.tex: texto completo de introducción propuesto, para revisar y luego integrar manualmente al plan.
- build_extraction_report.py: script que genera el informe Markdown a partir del texto extraído y las descripciones visuales.

## Fuente y alcance

La extracción proviene de C:/Users/PC/Downloads/main.pdf. Las diapositivas de ejemplo sobre QFT y CKKS se describen como material didáctico; no se incorporan como tema de la tesis. La estructura organizativa del borrador sigue los seis capítulos tentativos de Plan de Tesis/partes/06cierre.tex, no los cinco capítulos del ejemplo del seminario.

## Preservación

El archivo original Plan de Tesis/partes/04AspectosGenerales.tex no fue modificado. El nuevo LaTeX es un borrador para revisión. Antes de integrarlo, revisar las observaciones de citas y validar el vacío de investigación con la literatura pertinente.

## Regenerar la extracción

Desde esta carpeta, ejecutar:

    python build_extraction_report.py
