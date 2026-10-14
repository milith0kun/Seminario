"""Metricas de evaluacion para los escenarios E1/E2/E3.

Cubre los tres bloques exigidos por el plan de tesis:

  Linguistico   chrF++ (principal para lenguas aglutinantes), BLEU-4, ROUGE-L
                y similitud coseno semantica sobre embeddings multilingues.
  Fundamentacion  Faithfulness y Answer Relevance calculadas localmente.
  Alucinacion   Tasa de abstencion correcta sobre las sondas sin respaldo.

Nota sobre RAGAS: la libreria oficial requiere un LLM juez accesible por API.
Para mantener el pipeline reproducible y offline, este modulo implementa
aproximaciones deterministas de faithfulness y answer relevance, documentadas
en cada funcion. Los valores NO son intercambiables con los de RAGAS y deben
reportarse como tales.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Sequence

import numpy as np

_RE_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)

# Marcadores de abstencion: el modelo reconoce que no dispone del dato.
_PATRONES_ABSTENCION = [
    r"no (dispongo|tengo|cuento con|encuentro|hay)",
    r"no (puedo|podria) (confirmar|precisar|responder|indicar)",
    r"no (esta|figura|aparece) en (el|los|la|las)",
    r"no se (especifica|indica|menciona|precisa)",
    r"informacion no (disponible|proporcionada)",
    r"(consultar|consulte|revisar) (la )?(fuente|documento|portal) oficial",
    r"fuera del (material|corpus|contexto) (disponible|proporcionado)",
    r"desconozco",
    r"mana yachanichu",  # "no lo se" en quechua
]
_RE_ABSTENCION = re.compile("|".join(_PATRONES_ABSTENCION), re.IGNORECASE)


@dataclass
class MetricasLinguisticas:
    chrf_pp: float = 0.0
    bleu4: float = 0.0
    rouge_l: float = 0.0
    similitud_coseno: float = 0.0


@dataclass
class MetricasFundamentacion:
    faithfulness: float = 0.0
    answer_relevance: float = 0.0
    cobertura_contexto: float = 0.0


@dataclass
class MetricasEficiencia:
    ttft_ms: float = 0.0
    throughput_tok_s: float = 0.0
    latencia_total_ms: float = 0.0
    ram_pico_mb: float = 0.0
    tokens_generados: int = 0


def _tokens(texto: str) -> list[str]:
    return _RE_PALABRA.findall(texto.lower())


# --------------------------------------------------------------------------
# Bloque linguistico
# --------------------------------------------------------------------------

def chrf_pp(hipotesis: str, referencia: str) -> float:
    """chrF++ (F-score de n-gramas de caracter + unigramas/bigramas de palabra).

    Metrica principal del plan de tesis: al operar sobre caracteres captura la
    morfologia aglutinante del quechua, donde BLEU penaliza en exceso las
    variaciones de sufijacion.
    """
    from sacrebleu.metrics import CHRF

    if not hipotesis.strip() or not referencia.strip():
        return 0.0
    # word_order=2 es lo que convierte chrF en chrF++.
    return float(CHRF(word_order=2).sentence_score(hipotesis, [referencia]).score)


def bleu4(hipotesis: str, referencia: str) -> float:
    from sacrebleu.metrics import BLEU

    if not hipotesis.strip() or not referencia.strip():
        return 0.0
    # `effective_order` evita que una frase corta sin 4-gramas puntue 0 de forma
    # artificial, situacion frecuente en respuestas pedagogicas breves.
    return float(
        BLEU(effective_order=True).sentence_score(hipotesis, [referencia]).score
    )


def rouge_l(hipotesis: str, referencia: str) -> float:
    """ROUGE-L basado en la subsecuencia comun mas larga (F-measure)."""
    h, r = _tokens(hipotesis), _tokens(referencia)
    if not h or not r:
        return 0.0

    # Programacion dinamica sobre una sola fila: O(len(h) * len(r)) en tiempo,
    # O(len(r)) en memoria.
    previa = [0] * (len(r) + 1)
    for token_h in h:
        actual = [0] * (len(r) + 1)
        for j, token_r in enumerate(r, start=1):
            if token_h == token_r:
                actual[j] = previa[j - 1] + 1
            else:
                actual[j] = max(previa[j], actual[j - 1])
        previa = actual
    lcs = previa[-1]

    if lcs == 0:
        return 0.0
    precision, recall = lcs / len(h), lcs / len(r)
    return 100.0 * 2 * precision * recall / (precision + recall)


def similitud_coseno(vector_a: np.ndarray, vector_b: np.ndarray) -> float:
    na, nb = np.linalg.norm(vector_a), np.linalg.norm(vector_b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(vector_a, vector_b) / (na * nb))


# --------------------------------------------------------------------------
# Bloque de fundamentacion
# --------------------------------------------------------------------------

def faithfulness(respuesta: str, contextos: Sequence[str]) -> float:
    """Proporcion de contenido de la respuesta respaldado por los contextos.

    Aproximacion local de RAGAS faithfulness: en lugar de descomponer la
    respuesta en afirmaciones con un LLM juez, se segmenta en oraciones y cada
    una se considera respaldada si comparte suficiente lexico de contenido con
    algun fragmento recuperado.

    Umbral de respaldo por oracion: 0.5 de sus terminos de contenido presentes
    en el contexto. Sin contextos la metrica es 0 por definicion (nada que
    fundamentar), no 1.
    """
    if not contextos or not respuesta.strip():
        return 0.0

    vocab_contexto: set[str] = set()
    for c in contextos:
        vocab_contexto.update(_tokens(c))

    oraciones = [o for o in re.split(r"(?<=[.!?\n])\s+", respuesta) if o.strip()]
    if not oraciones:
        return 0.0

    respaldadas = 0
    evaluadas = 0
    for oracion in oraciones:
        terminos = [t for t in _tokens(oracion) if len(t) > 3]
        if len(terminos) < 3:
            continue  # Fragmentos demasiado cortos para juzgar respaldo.
        evaluadas += 1
        cobertura = sum(1 for t in terminos if t in vocab_contexto) / len(terminos)
        if cobertura >= 0.5:
            respaldadas += 1

    return respaldadas / evaluadas if evaluadas else 0.0


def answer_relevance(
    vector_consulta: np.ndarray, vector_respuesta: np.ndarray
) -> float:
    """Pertinencia de la respuesta respecto de la consulta.

    Aproximacion local de RAGAS answer_relevancy mediante similitud coseno
    directa entre los embeddings de consulta y respuesta, en lugar de generar
    preguntas inversas con un LLM.
    """
    return max(0.0, similitud_coseno(vector_consulta, vector_respuesta))


def cobertura_contexto(respuesta: str, contextos: Sequence[str]) -> float:
    """Fraccion de fragmentos recuperados que dejan huella lexica en la respuesta."""
    if not contextos:
        return 0.0
    tokens_respuesta = set(_tokens(respuesta))
    usados = 0
    for c in contextos:
        terminos = {t for t in _tokens(c) if len(t) > 4}
        if terminos and len(terminos & tokens_respuesta) / len(terminos) > 0.05:
            usados += 1
    return usados / len(contextos)


# --------------------------------------------------------------------------
# Bloque de alucinacion
# --------------------------------------------------------------------------

def es_abstencion(respuesta: str) -> bool:
    """True si la respuesta reconoce no disponer de la informacion."""
    return bool(_RE_ABSTENCION.search(respuesta or ""))


def inventa_entidad(respuesta: str) -> bool:
    """Heuristica de alucinacion factual sobre sondas sin respaldo.

    Marca la respuesta si afirma datos verificables con forma de cita oficial
    -codigos de resolucion, numeros de pagina, porcentajes, anios- sin haberse
    abstenido. Sobre las sondas, cualquiera de esos datos es necesariamente
    inventado, porque el corpus no los contiene.
    """
    if es_abstencion(respuesta):
        return False
    patrones = [
        r"\bR\.?\s?M\.?\s*N?[.º°]?\s*\d{2,4}",     # RM 1218-85-ED
        r"\bp[aá]g(?:ina)?\.?\s*\d+",               # pagina 42
        r"\b\d{1,3}\s?%",                            # 68 %
        r"\bart[ií]culo\s+\d+",                     # articulo 47
        r"\b(19|20)\d{2}\b",                        # anios
        r"\b\d{3,}\s+(estudiantes|docentes|alumnos)",
    ]
    return any(re.search(p, respuesta or "", re.IGNORECASE) for p in patrones)


def as_dict(objeto) -> dict:
    return asdict(objeto)


__all__ = [
    "MetricasLinguisticas",
    "MetricasFundamentacion",
    "MetricasEficiencia",
    "chrf_pp",
    "bleu4",
    "rouge_l",
    "similitud_coseno",
    "faithfulness",
    "answer_relevance",
    "cobertura_contexto",
    "es_abstencion",
    "inventa_entidad",
    "as_dict",
]
