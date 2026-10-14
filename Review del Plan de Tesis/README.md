# Revisión Sistemática de la Literatura Científica (SLR / Review Paper)

Este directorio contiene el **artículo formal de revisión sistemática de la literatura** (*State-of-the-Art Review Paper*) elaborado para fundamentar y contrastar el estado del arte del Plan de Tesis de la Escuela Profesional de Ingeniería Informática y de Sistemas (UNSAAC).

---

## Título del Artículo

> **Modelos de Lenguaje Pequeños (SLMs) y Generación Aumentada por Recuperación (RAG) en Dispositivos Móviles para Lenguas Originarias de Bajos Recursos:**  
> *Un Análisis Sistemático del Estado del Arte Orientado al Quechua Collao y la Educación Intercultural Bilingüe Desconectada*

---

## Estructura Modular del Artículo

```text
Review del Plan de Tesis/
├── Review_Plan_de_Tesis.tex         # Archivo maestro de compilación LaTeX
├── Review_Plan_de_Tesis.pdf         # PDF compilado y verificado (17 páginas)
├── README.md                        # Descripción y guía de compilación
├── imagenes/
│   └── logo.png                     # Escudo institucional de la UNSAAC
└── partes/
    ├── 00preambulo.tex              # Paquetes, tipografía, paleta científica y cajas
    ├── 01caratula_resumen.tex       # Carátula formal, resumen en español, abstract en inglés y TOC
    ├── 02introduccion.tex           # Sec. 1: Introducción, brecha digital andina y objetivos
    ├── 03metodologia_slr.tex        # Sec. 2: Metodología PRISMA 2020 y Kitchenham (RQ1--RQ4)
    ├── 04ejes_tematicos.tex         # Sec. 3: Análisis de los 4 ejes tecnológicos (SLM, RAG, PLN Quechua, PEFT)
    ├── 05taxonomia_y_comparativa.tex # Sec. 4: Taxonomía y matriz comparativa del Estado del Arte
    ├── 06brechas_investigacion.tex  # Sec. 5: Brechas críticas (Research Gaps) y oportunidades
    ├── 07conclusiones_roadmap.tex   # Sec. 6: Respuestas a RQs, conclusiones y hoja de ruta DSR
    ├── 08bibliografia.tex           # Configuración e inclusión bibliográfica
    └── Bibliografia.bib             # Base de datos BibTeX con fuentes científicas primarias
```

---

## Preguntas de Investigación Abordadas

* **RQ1 (Inferencia On-Device):** Requerimientos computacionales y límites de memoria de SLMs ($\le$ 3B) tras cuantización de 4 bits.
* **RQ2 (Edge RAG):** Almacenamiento vectorial embebido (\texttt{sqlite-vec}) y modelos compactos de embeddings sin conexión.
* **RQ3 (PLN en Quechua):** Morfología aglutinante, corpus paralelos (AmericasNLP) y normalización dialectal Quechua Collao (R.M. 1218-85-ED).
* **RQ4 (Ajuste Fino Eficiente):** Adaptación con QLoRA en hardware de bajo costo ($\le$ 4 GB VRAM) y preservación bilingüe.

---

## Instrucciones de Compilación

```bash
pdflatex -interaction=nonstopmode Review_Plan_de_Tesis.tex
bibtex Review_Plan_de_Tesis
pdflatex -interaction=nonstopmode Review_Plan_de_Tesis.tex
pdflatex -interaction=nonstopmode Review_Plan_de_Tesis.tex
```
