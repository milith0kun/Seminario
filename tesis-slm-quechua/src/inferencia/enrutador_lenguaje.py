from __future__ import annotations

import re

QU_MARKERS = {
    "imaynata",
    "ima",
    "mayqin",
    "allin",
    "yachay",
    "yachachiq",
    "wawa",
    "runa",
    "pacha",
    "yaku",
    "inti",
    "waspi",
    "kay",
    "chay",
    "ñuqa",
    "nuqa",
    "qam",
    "pay",
    "noqanchis",
    "rimay",
    "qillqay",
    "t'ikray",
    "kawsay",
    "pukllay",
}


def detect_language(text: str) -> str:
    tokens = re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ']+", text.lower())
    if not tokens:
        return "unknown"

    qu_hits = sum(1 for t in tokens if t in QU_MARKERS or t.endswith(("chu", "paq", "kuna", "ykuna")))
    es_hits = sum(1 for t in tokens if t in {"que", "es", "la", "el", "de", "para", "como", "porque", "una", "los"})

    if qu_hits >= 2 and es_hits >= 2:
        return "mixed_es_qu"
    if qu_hits >= 2 and qu_hits > es_hits:
        return "qu_collao"
    if es_hits >= 1 or qu_hits == 0:
        return "es"
    if qu_hits >= 1:
        return "qu_collao"
    return "unknown"


detectar_lenguaje = detect_language

