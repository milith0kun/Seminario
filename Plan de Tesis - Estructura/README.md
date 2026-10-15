# Plan de tesis: estructura y fuentes

Este directorio contiene el plan de tesis en LaTeX para la investigación sobre una arquitectura SLM--RAG con QLoRA para generación contextualizada en Quechua Collao. El documento aplica el proceso de seis bloques de la introducción y conserva una estructura modular para revisar el problema, los objetivos, las hipótesis y la metodología.

## Archivos principales

- `PlanTesis_Plantilla.tex`: archivo maestro que integra las partes del documento.
- `PlanTesis_Plantilla.pdf`: PDF generado desde el archivo maestro; el número de páginas depende de la compilación.
- `partes/01caratula.tex`: portada institucional y título seleccionado.
- `partes/02resumen.tex`: resumen y abstract.
- `partes/03indices.tex`: índice general, índices de figuras, tablas, algoritmos, abreviaturas, símbolos, ecuaciones y anexos, además del glosario.
- `partes/04Introduccion.tex`: introducción redactada en prosa continua, siguiendo la secuencia lógica de los seis bloques.
- `partes/04AspectosGenerales.tex`: planteamiento del problema, objetivos, hipótesis, justificación, alcances y matriz de consistencia.
- `partes/05EstadoDelArte.tex` y `partes/05MarcoTeorico.tex`: revisión de antecedentes y fundamentos teóricos.
- `partes/05bMetodologia.tex`: contenido desarrollado de diseño, variables, muestra, instrumentos, procedimiento y evaluación.
- `partes/05cFactibilidad.tex`: estructura del capítulo IV, reservada para completar después de metodología.
- `partes/06AspectosAdministrativos.tex`: cronograma, presupuesto y equipo; se conserva como fuente para una revisión posterior y no se integra en este avance.
- `partes/Bibliografia.bib`: referencias administradas con `biblatex` y estilo APA 7.
- `partes/08Anexos.tex`: matriz lógica y fichas de evaluación propuestas.
- `../aplicacion_intro_plan_tesis/`: extracción del seminario, imágenes de sus 37 diapositivas y presentación que explica la aplicación. Esta es la carpeta de referencia para el proceso.

## Compilación

Desde este directorio, compilar el archivo maestro con:

```bash
latexmk -pdf PlanTesis_Plantilla.tex
```

El proyecto usa `biblatex` con backend Biber. `latexmk` ejecuta las pasadas bibliográficas necesarias cuando las herramientas están instaladas.

## Criterios de edición

- Mantener el título y los objetivos alineados con las presentaciones de Título y Objetivos.
- Tratar QLoRA como una condición experimental sujeta a la viabilidad del hardware, sin anticipar resultados.
- Registrar procedencia, licencia, idioma y variedad de las fuentes lingüísticas.
- No afirmar como definitiva la brecha de investigación mientras la revisión bibliográfica siga siendo preliminar.
- Distinguir las métricas automáticas de similitud de una validación de calidad lingüística y factual.
- Conservar los índices y referencias cruzadas actualizados al editar figuras, tablas, algoritmos, ecuaciones o anexos.
