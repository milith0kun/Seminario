# Seminario de Investigación II — Plan de tesis

## Entregables principales

- **Guía para estudiar y exponer:** `output/pdf/Guia_Estudio_Sustentacion_Plan_Tesis.pdf`, organizada por diapositiva con conceptos clave y preguntas probables.
- **Plan de tesis en PDF:** `Plan de Tesis - Estructura/PlanTesis.pdf`.
- **Fuente editable del plan:** `Plan de Tesis - Estructura/PlanTesis_Plantilla.tex`, con sus capítulos en `Plan de Tesis - Estructura/partes/`.
- **Formato del plan:** maquetación APA 7 en español con tipografía Times equivalente, márgenes de 2.54 cm, doble espacio, sangría de primera línea, folio superior derecho desde la portada, títulos a 12 pt, tablas y figura con rótulos APA, citas y referencias en `biblatex`/Biber y apéndices A–D; conserva la numeración institucional de capítulos.
- **Introducción del plan de tesis:** es el Capítulo I y sigue el esquema de contexto, tecnología o método, vacío, problema, propuesta, objetivos, hipótesis, justificación, alcances y organización. Las fuentes y la extracción de las diapositivas se conservan en `Plan de Tesis - Estructura/`.
- **Diapositivas:** `diapositiva/index.html`; su PDF es `diapositiva/index.pdf`. La presentación tiene 19 diapositivas y llega hasta Metodología.
- **Código LaTeX comprimido:** `PlanTesis_Codigo_LaTeX.zip`, con el archivo maestro y las partes que generan el PDF, junto con bibliografía y logotipo. La fuente administrativa no integrada se conserva aparte.
- **Dirección del repositorio:** `GitHub_URL.txt`.
- **Carpeta para Classroom:** `output/Entrega_Classroom/`, con las diapositivas PDF, el plan PDF, el ZIP LaTeX y el TXT con la URL de GitHub.

## Compilar el plan de tesis

Desde `Plan de Tesis - Estructura/`, ejecutar:

```bash
latexmk -pdf PlanTesis_Plantilla.tex
```

El proyecto usa `biblatex` con backend Biber y requiere LaTeX, Biber y los paquetes indicados en `partes/00preambulo.tex`.

## Contenido del plan

El documento desarrolla la portada, resumen e índices preliminares. El Capítulo I es Introducción y sigue el esquema solicitado; el Capítulo II reúne marco teórico y estado del arte, y el Capítulo III integra metodología, variables y operacionalización. El Capítulo IV, estudio de factibilidad, se conserva solo como esquema para una etapa posterior; los aspectos administrativos no forman parte de este avance.

## Presentación

`diapositiva/index.html` es la fuente de la diapositiva seleccionada. El PDF se exporta desde ese archivo y conserva el mismo orden y contenido; no se utiliza la presentación Beamer separada.

El repositorio se limita a estos entregables y a los archivos `README.md`, `AGENTS.md`, `.gitignore` y `.gitattributes` que los describen y mantienen ordenados. Las demás carpetas de trabajo quedan en el equipo local y no se publican.

## Criterios académicos

- Mantener alineados el problema, objetivos, hipótesis y metodología.
- Tratar QLoRA como una condición experimental sujeta a viabilidad técnica.
- No anticipar resultados ni inventar datos, citas o referencias.
- Identificar la procedencia, licencia, idioma y variedad de las fuentes lingüísticas.
