# Extracción del seminario y aplicación al plan de tesis

Esta carpeta conserva la extracción del PDF de seminario y el borrador de seis bloques utilizado para corregir la introducción del plan SLM–RAG sobre Quechua Collao.

## Material conservado

- extraccion_37_diapositivas.md: transcripción y descripción visual de las 37 diapositivas, con enlaces a sus imágenes.
- seminario_extraido.txt: texto extraído del PDF.
- diapositivas/: imágenes PNG de las 37 páginas, numeradas del 01 al 37.
- introduccion_plan_tesis_fragmento.tex: borrador de referencia del proceso de introducción.
- build_extraction_report.py: script que genera el Markdown de extracción a partir del texto y las descripciones visuales.

## Aplicación en el plan

La introducción corregida está integrada en ../partes/04AspectosGenerales.tex. Sus siete referencias están añadidas a ../partes/Bibliografia.bib. El documento completo actualizado es ../PlanTesis_Plantilla.pdf.

La extracción proviene de C:/Users/PC/Downloads/main.pdf. Las diapositivas sobre QFT y CKKS se conservan como material del seminario y no se incorporan como tema de la tesis.

## Regenerar la extracción

Desde esta carpeta, ejecutar:

    python build_extraction_report.py
