# Diapositivas del plan de tesis

`index.html` es la fuente de la presentación seleccionada. `index.pdf` es su versión estática para entrega y contiene las mismas 19 diapositivas.

El contenido se detiene en Metodología. No incluye cronograma, estudio de factibilidad desarrollado, resultados ni conclusiones de una investigación concluida.

Los diagramas y el logotipo usados por la presentación se guardan junto al HTML. Para regenerar el PDF se puede usar `scripts/export-pdf.sh` con Bash, Node.js y npm:

```bash
bash scripts/export-pdf.sh /d/Proyectos/Seminario/diapositiva/index.html /d/Proyectos/Seminario/diapositiva/index.pdf
```

La exportación mantiene las figuras vectoriales y no conserva las animaciones del HTML.
