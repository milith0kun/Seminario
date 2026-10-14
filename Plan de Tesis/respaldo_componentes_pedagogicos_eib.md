# Respaldo de Componentes Pedagógicos, Andamiaje y Validación Docente EIB

> **Fecha de respaldo:** Octubre 2026  
> **Motivo:** Reenfoque formal del Plan de Tesis al área estricta de **Ingeniería Informática y de Sistemas (IA / PLN / Computación)**. Se eliminan del plan principal los elementos de psicología educativa, andamiaje cognitivo, diseño curricular de primaria, y validación mediante rúbricas con docentes EIB, centralizando el aporte en la **arquitectura técnica SLM + RAG y la adaptación/entrenamiento de matrices de pesos (QLoRA/PEFT)** con métricas computacionales automáticas.
> Este archivo conserva íntegramente las redacciones originales por si se requieren consultar o reutilizar en el futuro.

---

## 1. De `partes/04AspectosGenerales.tex`

### 1.1 Redacción del Problema Centrado en Docente y Aula Escolar
```latex
La educación rural bajo el modelo de Educación Intercultural Bilingüe (EIB) en el Perú enfrenta una profunda brecha de recursos y herramientas tecnológicas adaptadas. A pesar de que el sistema EIB atiende a más de 1,2 millones de estudiantes en el país \citep{minedu2018}, su implementación en el ámbito rural se ve limitada por la falta de conectividad digital...

Por otro lado, aunque el avance de la inteligencia artificial generativa ha popularizado el uso de asistentes virtuales para el aprendizaje, las soluciones comerciales son inviables para las escuelas rurales EIB. Esto se debe a tres limitaciones estructurales: (a) requieren conexión permanente a internet para consultar modelos remotos en la nube, (b) carecen de representación real y alineación con la variedad Quechua Collao, y (c) no están adaptadas al currículo oficial del Ministerio de Educación ni siguen estrategias instruccionales de andamiaje formativo.

En consecuencia, existe una brecha técnica y pedagógica no resuelta: la ausencia de un asistente educativo bilingüe español--Quechua Collao que funcione 100% offline, que integre un enrutamiento lingüístico automático para consultas bilingües, y que recupere localmente contenidos curriculares validados mediante una arquitectura de modelo compacto y RAG local.
```

### 1.2 Nodo de Efecto en el Árbol de Problemas
```latex
\node[trojo, minimum height=1.5cm] (e4) at (6.6,3.0) {Docentes bilingües sin herramientas de andamiaje pedagógico complementario};
```

### 1.3 Alcance y Limitación Pedagógica
```latex
\item \textbf{Alcance pedagógico:} El primer ciclo de validación se centrará en consultas curriculares de 3.° a 6.° grado de primaria, priorizando las áreas de Comunicación y Ciencia y Tecnología según la disponibilidad de materiales EIB bilingües. Las respuestas del sistema seguirán el principio de andamiaje cognitivo, priorizando explicaciones graduales sobre respuestas directas.

\item \textbf{Validación pedagógica y lingüística:} La evaluación de pertinencia y adecuación dependerá de la validación del docente especialista EIB y del especialista lingüístico en la variedad Quechua Collao.
```

### 1.4 Matriz de Consistencia Previa (Fila Docente)
```latex
Requerimientos lingüísticos, pedagógicos y tecnológicos & Curar y estructurar la base documental bilingüe & Fase exploratoria (sin VD directa) & Análisis documental EIB; validación con docente especialista \\
Evaluación de la calidad del prototipo & Evaluar mediante métricas técnicas, lingüísticas y rúbricas & VD4--VD8: chrF++, \textit{faithfulness}, adecuación dialectal, andamiaje, pertinencia curricular & chrF++, SacreBLEU, RAGAS; rúbricas de juicio de expertos \\
```

---

## 2. De `partes/InformeVariables.tex` y `partes/05MarcoTeorico.tex`

### 2.1 Variables Dependientes Pedagógicas (VD7 y VD8)
```latex
\subsubsection{Dimensión 3: Pertinencia Pedagógica e Intercultural (Cualitativa)}
Mide el valor educativo y la pertinencia intercultural del andamiaje conversacional.
\begin{itemize}
    \item \textbf{Nivel de andamiaje formativo (Cualitativa ordinal):} Capacidad del asistente de guiar progresivamente al alumno (pregunta orientadora, pistas, explicación bilingüe y aplicación) en lugar de limitarse a proveer una traducción directa o respuesta directa literal. Calificado por el docente especialista en EIB (Escala Likert de 1 a 5).
    \item \textbf{Relevancia y pertinencia curricular (Cualitativa ordinal):} Adecuación pedagógica del contenido factual recuperado y explicado en las áreas de Comunicación y Ciencia y Tecnología para el nivel primario (3.° a 6.° grado). Calificado por el docente especialista en EIB (Escala Likert de 1 a 5).
\end{itemize}

% Filas de la tabla de operacionalización:
\textbf{VD7: Nivel de andamiaje} & Cualitativa ordinal & Pertinencia pedagógica & Estructura gradual de ayuda pedagógica (preguntas, pistas y ejemplos). & Escala Likert de 1 a 5 (Progresión cognitiva y bilingüismo) & Rúbrica de evaluación pedagógica para docente EIB. \\
\textbf{VD8: Pertinencia curricular} & Cualitativa ordinal & Pertinencia pedagógica & Adecuación temática y lingüística a las áreas de Comunicación y CyT. & Escala Likert de 1 a 5 (Grado de correspondencia oficial) & Rúbrica de evaluación curricular para docente EIB. \\
```

### 2.2 Marco Conceptual: Sistemas de Tutoría Inteligente (ITS) y Andamiaje
```latex
Los Sistemas de Tutoría Inteligente (ITS, \textit{Intelligent Tutoring Systems}) son sistemas informáticos diseñados para proporcionar instrucción personalizada adaptada al nivel de comprensión del estudiante, sin intervención humana directa en tiempo real. Los ITS modernos basados en modelos de lenguaje incorporan principios pedagógicos como el andamiaje cognitivo (\textit{scaffolding}), que consiste en ofrecer apoyos estructurados que el aprendiz retira progresivamente a medida que adquiere competencia; la Zona de Desarrollo Próximo (ZDP) de \citet{Vygotsky1978}, que delimita el rango de tareas que el estudiante puede realizar con guía pero no de forma autónoma; y el \textit{feedback} formativo, que orienta al estudiante hacia la comprensión correcta en lugar de limitarse a confirmar o refutar respuestas.

El asistente educativo propuesto se inscribe en este marco conceptual. Su propósito no es reemplazar al docente bilingüe sino proveer un apoyo adicional disponible fuera del horario de clase y en entornos sin conectividad, respondiendo consultas curriculares con un tono pedagógico adecuado a la edad y al nivel educativo del usuario. \citet{Levonian2025} establecen que los sistemas de tutoría generativa deben diseñarse para generar interacciones seguras y relevantes, priorizando el andamiaje cognitivo sobre la simple provisión de respuestas directas, criterio que guía el diseño del pipeline de generación del presente proyecto.
```

### 2.3 Unidad de Validación Humana
```latex
\item \textbf{Unidad de validación humana:} Evaluadores especializados conformados por: (i)~un (1) docente especialista en Educación Intercultural Bilingüe (EIB) activo, encargado de definir las pautas pedagógicas del asistente y validar la adecuación del andamiaje formativo; y (ii)~un (1) especialista lingüístico en la variedad Quechua Collao (hablante nativo), encargado de validar la adecuación dialectal y ortográfica de las respuestas generadas.
```

---

## 3. De `partes/05bFactibilidad.tex`

### 3.1 Estrategia de Andamiaje Gradual
```latex
El asistente no es un traductor automático ni un chatbot genérico: es una herramienta de \textbf{andamiaje cognitivo bilingüe}. Para lograr esto, la información pedagógica que alimenta el sistema proviene de fuentes específicas y se estructura con una estrategia instruccional definida:
- Guías docentes EIB: Orientaciones metodológicas del MINEDU para docentes de aulas bilingües.
El sistema seguirá un patrón de andamiaje gradual en sus respuestas, evitando dar respuestas directas y priorizando la construcción progresiva del conocimiento.
```

### 3.2 Dependencias Operativas
```latex
Sin embargo, mantiene dos dependencias operativas serias: la coordinación con docentes o especialistas EIB para la validación pedagógica, y el acceso a materiales curriculares en escenarios de prueba con pertinencia lingüística responsable.
```

---

## 4. De `partes/06cierre.tex` (Cronograma y Entregables)
```latex
\ganttbar{Validación con docente EIB y lingüista nativo}{5}{5} \\
Validación con docente EIB y lingüista nativo & Diciembre 2026 & M5 \\
Presentación de resultados cuantitativos (...) y cualitativos (rúbricas Likert de docente EIB y lingüista)
```
