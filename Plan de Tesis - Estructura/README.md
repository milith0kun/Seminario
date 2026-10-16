# Plan de tesis: estructura y fuentes

Este directorio contiene el plan de tesis en LaTeX para evaluar el efecto de adaptar mediante QLoRA un modelo de lenguaje compacto en la generación de respuestas breves a preguntas cotidianas en quechua sureño, con atención a las variedades chanka y collao. La propuesta no implementa RAG ni presenta resultados experimentales. La introducción es el Capítulo I y organiza sus seis bloques con el esquema mostrado por el usuario.

## Archivos principales

- `PlanTesis_Plantilla.tex`: archivo maestro que integra las partes del documento.
- `PlanTesis.pdf`: PDF generado desde el archivo maestro; el número de páginas depende de la compilación.
- `partes/00preambulo.tex`: formato tipográfico y de párrafo, folios, niveles de títulos, tablas, figuras y citas según APA 7, armonizado con la estructura institucional numerada.
- `partes/01caratula.tex`: portada institucional y título seleccionado.
- `partes/02resumen.tex`: resumen y abstract.
- `partes/03indices.tex`: índice general, índices de tablas, figuras, algoritmos, abreviaturas, símbolos, ecuaciones y apéndices/anexos, además del glosario.
- `partes/04Introduccion.tex`: Capítulo I, organizado con el esquema de las imágenes: contexto, tecnología o método, vacío, problema, propuesta, objetivos, hipótesis, justificación, alcances y organización de la tesis.
- `partes/04AspectosGenerales.tex` y `partes/04Hipotesis.tex`: fragmentos del Capítulo I para problema, propuesta, objetivos, hipótesis, justificación y alcances.
- `partes/05EstadoDelArte.tex` y `partes/05MarcoTeorico.tex`: Capítulo II, revisión de antecedentes y fundamentos teóricos.
- `partes/05bMetodologia.tex`: Capítulo III, con enfoque, tipo y diseño; unidades de análisis, muestra, recursos, instrumentos, procedimiento, análisis y consideraciones éticas.
- `partes/05VariablesOperacionalizacion.tex`: variables, operacionalización, criterio de aceptabilidad y matriz de consistencia integrados en Metodología.
- `partes/05cFactibilidad.tex`: estructura del capítulo IV, conservada como esquema para desarrollar después de metodología.
- `partes/06AspectosAdministrativos.tex`: fuente administrativa conservada en la carpeta del repositorio para revisión posterior; no se integra ni se incluye en el ZIP de este avance.
- `partes/Bibliografia.bib`: referencias administradas con `biblatex` y estilo APA 7.
- `partes/08Anexos.tex`: apéndices A–D con la matriz de consistencia, ficha técnica, rúbrica y plantilla del corpus.
- `Aplicacion_Introduccion_Plan_Tesis/`: extracción y las imágenes de las 37 diapositivas que documentan el proceso aplicado en la introducción del plan.

## Compilación

Desde este directorio, compilar el archivo maestro con:

```bash
latexmk -pdf PlanTesis_Plantilla.tex
```

El proyecto usa `biblatex` con backend Biber. `latexmk` ejecuta las pasadas bibliográficas necesarias cuando las herramientas están instaladas. En Windows, esta instalación de `latexmk` requiere Perl; como alternativa, ejecutar `pdflatex`, `biber` y dos pasadas adicionales de `pdflatex`.

## Criterios de edición

- Mantener la coherencia interna entre título, problemas, objetivos, hipótesis, variables y metodología. La presentación de aplicación de la introducción se alinea con esta versión; la presentación pública `diapositiva/index` requiere su revisión propia antes de exponerse junto con el plan.
- Tratar QLoRA como una condición experimental sujeta a la viabilidad del hardware, sin anticipar resultados.
- Registrar procedencia, licencia, idioma y variedad de las fuentes lingüísticas.
- No afirmar como definitiva la brecha de investigación mientras la revisión bibliográfica siga siendo preliminar.
- Distinguir las métricas automáticas de similitud de una validación de calidad lingüística y factual.
- Conservar los índices y referencias cruzadas actualizados al editar figuras, tablas, algoritmos, ecuaciones o anexos.
