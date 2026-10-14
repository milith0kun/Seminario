# Plantilla Estructural del Plan de Tesis (UNSAAC)

Esta carpeta contiene la **plantilla canónica y modular** para la formulación de planes de tesis en la Escuela Profesional de Ingeniería Informática y de Sistemas de la Universidad Nacional de San Antonio Abad del Cusco (UNSAAC), estructurada con enfoque metodológico riguroso (*Design Science Research* / Enfoque Cuantitativo).

---

## Estructura Modular de Archivos

```text
Plan de Tesis - Estructura/
├── PlanTesis_Plantilla.tex         # Archivo maestro de compilación
├── PlanTesis_Plantilla.pdf         # PDF generado y validado (19 páginas)
├── README.md                       # Guía de uso de la plantilla
├── imagenes/
│   └── logo.png                    # Escudo oficial de la UNSAAC
└── partes/
    ├── 00preambulo.tex             # Paquetes, márgenes, colores y entorno de pautas
    ├── 01caratula.tex              # Carátula oficial parametrizada
    ├── 02resumen.tex               # Estructura del resumen y palabras clave
    ├── 03indices.tex               # Índice general, índice de figuras y de tablas
    ├── 04AspectosGenerales.tex     # Cap. 1: Problema, formulación, objetivos, justificación
    ├── 05EstadoDelArte.tex         # Cap. 2: Antecedentes internacionales, nacionales, matriz
    ├── 05MarcoTeorico.tex          # Cap. 3: Bases teóricas y glosario de términos
    ├── 05bMetodologia.tex          # Cap. 4: Enfoque, DSR, operacionalización de variables
    ├── 06AspectosAdministrativos.tex # Cap. 5: Cronograma Gantt (pgfgantt) y presupuesto
    ├── 07bibliografia.tex          # Inclusión de referencias bibliográficas
    ├── 08Anexos.tex                # Anexos: Matriz de consistencia y ficha de pruebas
    └── Bibliografia.bib            # Base de datos BibTeX metodológica
```

---

## Cómo Compilar el Documento

Desde la terminal en esta carpeta:

```bash
pdflatex -interaction=nonstopmode PlanTesis_Plantilla.tex
bibtex PlanTesis_Plantilla
pdflatex -interaction=nonstopmode PlanTesis_Plantilla.tex
pdflatex -interaction=nonstopmode PlanTesis_Plantilla.tex
```

---

## Características de la Plantilla

1. **Cajas de Pauta Metodológica (`pautaMetodologica`):** Cada sección incluye recuadros estilizados con pautas precisas sobre qué redactar y cómo cumplir las normas universitarias.
2. **Diagramas Vectoriales en TikZ:** Árbol de problemas parametrizado y editable sin necesidad de software externo.
3. **Cronograma Vectorial (`pgfgantt`):** Diagrama de Gantt editable organizado por fases de investigación DSR.
4. **Matriz de Operacionalización y Consistencia:** Tablas formateadas con `booktabs`, `tabularx` y `threeparttable` bajo lineamientos APA 7.
5. **Bibliografía Automatizada:** Integración completa con BibTeX mediante `natbib` (`\citep{...}`, `\citet{...}`).

## Aplicación del seminario a la introducción

La extracción textual y visual de las 37 diapositivas de `main.pdf` se conserva en `Aplicacion_Introduccion_Plan_Tesis/`. El proceso de seis bloques está aplicado en la introducción de `partes/04AspectosGenerales.tex`, con sus citas en `partes/Bibliografia.bib`; el PDF completo actualizado es `PlanTesis_Plantilla.pdf`.
