# Seminario de Investigación II — Plan de tesis

## Entregables principales

- **Plan de tesis estructurado:** fuente LaTeX y PDF en `Plan de Tesis - Estructura/`.
- **Diapositivas:** la presentación seleccionada es `diapositiva/index.html`; su PDF es `diapositiva/index.pdf`. El contenido llega hasta Metodología y el PDF refleja las 19 diapositivas actuales.
- **Código LaTeX comprimido:** `PlanTesis_Codigo_LaTeX.zip`, con el archivo maestro, las partes incluidas, la bibliografía y el logotipo requerido para compilar.
- **Dirección del repositorio:** `GitHub_URL.txt`.

## Compilar el plan de tesis

Desde `Plan de Tesis - Estructura/`, ejecutar:

```bash
latexmk -pdf PlanTesis_Plantilla.tex
```

El proyecto usa `biblatex` con backend Biber y requiere LaTeX, Biber y los paquetes indicados en `partes/00preambulo.tex`.

## Contenido del plan

El documento desarrolla la portada, resumen, índices, introducción, planteamiento del problema, objetivos, hipótesis, justificación, estado del arte, marco teórico y metodología. El capítulo de factibilidad se conserva como esquema para desarrollo posterior; los aspectos administrativos no forman parte de este avance.

## Presentación

`diapositiva/index.html` es la fuente de la diapositiva seleccionada. El PDF se exporta desde ese archivo y conserva el mismo orden y contenido; no se utiliza la presentación Beamer separada.

## Criterios académicos

- Mantener alineados el problema, objetivos, hipótesis y metodología.
- Tratar QLoRA como una condición experimental sujeta a viabilidad técnica.
- No anticipar resultados ni inventar datos, citas o referencias.
- Identificar la procedencia, licencia, idioma y variedad de las fuentes lingüísticas.
