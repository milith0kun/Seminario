from pathlib import Path
import re

root = Path(r"D:\Proyectos\Seminario\aplicacion_intro_plan_tesis")
raw = (root / "seminario_extraido.txt").read_text(encoding="utf-8")
pages = raw.split("\f")[:37]

visual = [
"Portada institucional de la UNSAAC. Presenta el Seminario de Investigación II, el tema «Tesis: introducción», la facultad y departamento, el docente y la fecha (Cusco, 9 de octubre de 2026).",
"Diapositiva de tabla de contenidos con una sola unidad: «1 Tesis introducción».",
"Portada gráfica del método de seis bloques. El título anuncia la arquitectura de una introducción científica; seis cubos azules enlazados representan los bloques.",
"Diagrama de embudo o recorrido de los seis bloques: contexto y problema general; tecnología o método; vacío de investigación; problema específico; propuesta, objetivo y justificación; organización de la tesis. Una nota destaca que cada bloque debe cumplir una función propia y mantener alineación lógica.",
"Infografía del bloque 1: pasar de la visión general a la dificultad y al tema concreto en cuatro movimientos: campo e importancia, avance o necesidad, dificultad general y transición al tema específico.",
"Diapositiva textual que desarrolla los cuatro movimientos A–D del contexto y problema general.",
"Ejemplo redactado del bloque 1 sobre aprendizaje automático, datos sensibles, confidencialidad y mecanismos de protección. Es un ejemplo de tema, no contenido de la tesis Quechua Collao.",
"Infografía del bloque 2. Usa engranajes y apartados para métodos existentes, fundamento de la tecnología elegida, evidencia previa y limitaciones. Contrasta afirmaciones sustentables con afirmaciones que no deben hacerse sin evidencia.",
"Diapositiva textual que explica los cuatro componentes A–D de tecnología o método.",
"Ejemplo sobre cifrado homomórfico, Transformada Cuántica de Fourier (QFT) y aprendizaje automático. Propone evaluar la integración atendiendo a representaciones, operaciones, desempeño predictivo, costo y reproducibilidad. Es un ejemplo ajeno al tema de la tesis.",
"Diagrama del vacío de investigación con áreas que convergen alrededor de «El vacío» y una secuencia deductiva: síntesis, comparación crítica, limitación y delimitación. Advierte que no se invente un problema; debe identificarse una pregunta abierta con evidencia.",
"Lista de formas posibles de vacío: algoritmo no evaluado en ciertas condiciones; tecnologías estudiadas por separado sin integración; resultados no comparables; costo, precisión o escalabilidad poco conocidos; arquitectura sin validación experimental.",
"Tabla de cuatro etapas para establecer el vacío: síntesis de antecedentes, comparación crítica, identificación de la limitación y delimitación del vacío.",
"Diapositiva textual con los pasos A–D: conocimientos establecidos, líneas relacionadas, brecha por verificar con artículos/experimentos/limitaciones/trabajos futuros y delimitación de la evaluación.",
"Ejemplo de síntesis sobre aprendizaje automático protegido mediante criptografía y computación cuántica. Indica que los resultados separados no prueban la viabilidad de integrar QFT y CKKS; deben revisarse datos, operaciones, desempeño y costo.",
"Tabla diagnóstica de antecedentes: autor/año, objetivo, método, condiciones, métricas, resultados y limitaciones. Agrupa estudios A/B/C, deja datos desconocidos por completar y conduce a una pregunta sobre la integración de QFT+CKKS en condiciones comparables.",
"Gráfico del bloque 4 que delimita el problema específico mediante controles para objeto de estudio, condiciones o entorno, desempeño, costo y protección/privacidad.",
"Diapositiva textual con los cuatro componentes del problema específico: objeto, desempeño y comparación, costo computacional, y condiciones de privacidad y evaluación.",
"Ejemplo de delimitación para una arquitectura QFT+CKKS durante entrenamiento de modelos de aprendizaje automático. Separa desempeño predictivo, costos y qué operaciones se ejecutan cifradas, junto con los supuestos de protección.",
"Pregunta modelo sobre el comportamiento experimental de una arquitectura QFT+CKKS frente a métodos de referencia en desempeño predictivo, costo computacional y privacidad.",
"Ilustración que presenta «la anatomía de una pregunta de investigación»: objeto de estudio, criterios de evaluación, aplicación concreta y comparación verificable.",
"Diapositiva que define la propuesta de investigación y enumera acciones posibles: diseñar una arquitectura, desarrollar un algoritmo, construir un prototipo, optimizar un procedimiento, comparar métodos o demostrar una propiedad. La acción debe coincidir con el aporte real.",
"Esquema A–D para presentar una propuesta: acción, tecnología, aplicación/contexto y evaluación mediante experimentos, comparaciones y métricas.",
"Ejemplo redactado de propuesta que integra QFT y CKKS para entrenamiento de modelos, con condiciones experimentales y evaluación de desempeño, costo, protección y métodos de referencia.",
"Fórmula para redactar el objetivo general: verbo en infinitivo + objeto de estudio + tecnología o método + finalidad + criterios de evaluación.",
"Ejemplo de objetivo con «evaluar experimentalmente». La diapositiva relaciona el verbo principal con la obligación de realizar experimentos y validar la arquitectura.",
"Diapositiva textual que separa la justificación científica, metodológica y tecnológica.",
"Ejemplo breve de justificación científica, metodológica y tecnológica aplicado a la arquitectura QFT+CKKS.",
"Recomendación de anticipar en la introducción el enfoque metodológico sin desarrollar parámetros, equipos, procedimientos o análisis estadísticos, que corresponden al capítulo metodológico.",
"Diagrama de tres piezas conectadas: qué se hará (propuesta), qué se busca alcanzar (objetivo) y por qué importa (justificación). Advierte evitar la redundancia.",
"Diagrama-fórmula del objetivo general. Asocia el verbo, objeto, tecnología/método, finalidad y criterios de evaluación a un ejemplo QFT+CKKS.",
"Diagrama del trípode de valor de la justificación: aporte científico (conocimiento), metodológico (protocolos) y tecnológico (problema de ingeniería), vinculados a contribuciones y aplicaciones.",
"Infografía del bloque 6 con el mapa de cinco capítulos del ejemplo: introducción; antecedentes y teoría; metodología/arquitectura; resultados; conclusiones. Es la estructura del ejemplo de clase, no necesariamente la del plan de tesis.",
"Texto que desarrolla la función de cada uno de los cinco capítulos del ejemplo. El inicio de las palabras «Capítulo» aparece recortado en la diapositiva/PDF y se conserva como limitación de extracción.",
"Diagrama de la cadena argumental: contexto → tecnología/método → vacío → problema específico → propuesta/objetivo/justificación → organización. Señala que cada bloque prepara el siguiente.",
"Lista de verificación con seis casillas, una por bloque: necesidad, tecnología y evaluación, evidencia del vacío, pregunta medible, objetivo alineado y mapa de capítulos. Cierra con una frase sobre la escritura académica como ingeniería de sistemas.",
"Diapositiva final titulada «Referencias Bibliográficas I». En el PDF recibido no se distinguen referencias bibliográficas en el cuerpo de esta página."
]

def clean_page(page):
    kept = []
    for line in page.replace("\r", "").split("\n"):
        stripped = line.strip()
        if not stripped:
            kept.append("")
            continue
        if ("Msc. Raul Huillca Huallparimachi" in line
                and "SEMINARIO DE INVESTIGACION II" in line
                and re.search(r"\b\d+\s*/\s*37\b", line)):
            continue
        if re.fullmatch(r"[\s./0-9]+", line) and line.count(".") >= 4:
            continue
        line = re.sub(r"\s+(?:\.\s*){4,}.*$", "", line)
        line = re.sub(r"\s+\b\d+\s*/\s*37\b.*$", "", line)
        if line.strip():
            kept.append(line.rstrip())
    return "\n".join(kept).strip()

out = [
    "# Extracción y revisión visual: Seminario de Investigación II",
    "",
    "**Archivo de origen:** C:/Users/PC/Downloads/main.pdf",
    "",
    "**Alcance:** 37 diapositivas. En cada una se conserva el texto extraíble del PDF y se añade una descripción de los elementos visuales. Las imágenes completas están en diapositivas/slide-01.png a slide-37.png.",
    "",
    "**Nota de lectura:** el texto corresponde a extracción digital del PDF, no a una transcripción corregida. Se preservan giros y cortes del original cuando son legibles. Las diapositivas gráficas pueden contener rótulos que el extractor no reconoce; por eso cada página incluye una descripción visual. Las diapositivas 7, 10, 15, 19, 20, 24, 26 y 28 usan QFT/CKKS como ejemplos del curso, no como tema de la tesis SLM–RAG para Quechua Collao.",
    "",
    "## Diapositivas",
    ""
]
for i, page in enumerate(pages):
    txt = clean_page(page)
    out.extend([
        f"### Diapositiva {i+1:02d}",
        "",
        f"**Imagen:** [slide-{i+1:02d}.png](diapositivas/slide-{i+1:02d}.png)",
        "",
        f"**Contenido visual:** {visual[i]}",
        "",
        "**Texto extraído:**",
        ""
    ])
    if txt:
        out.extend(["    " + line for line in txt.splitlines()])
        out.append("")
    else:
        out.extend(["*[Sin texto seleccionable en el extractor; revisar la imagen enlazada.]*", ""])
out.extend([
    "## Observaciones de aplicación",
    "",
    "- La secuencia del seminario es: contexto general → tecnología/método → vacío respaldado → problema delimitado → propuesta, objetivo y justificación → organización del documento.",
    "- Las diapositivas de ejemplo sobre QFT y CKKS explican la forma de razonar; sus tecnologías y afirmaciones no se trasladan al tema de esta tesis.",
    "- La última diapositiva muestra el encabezado de referencias, pero no contiene datos bibliográficos legibles en el archivo recibido.",
    ""
])
(root / "extraccion_37_diapositivas.md").write_text("\n".join(out), encoding="utf-8")
print(f"Informe creado: {root / 'extraccion_37_diapositivas.md'}")
print(f"Diapositivas procesadas: {len(pages)}; descripciones visuales: {len(visual)}")
