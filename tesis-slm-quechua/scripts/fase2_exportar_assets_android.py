"""Exporta el indice vectorial y el conjunto de evaluacion como assets Android.

La app ejecuta el RAG on-device con vectores precomputados: los embeddings del
corpus curricular y de las consultas de evaluacion se calculan aqui una sola
vez y viajan dentro del APK. En el dispositivo, la recuperacion es un producto
punto entre vectores normalizados, es decir, similitud de coseno real.

Para consultas libres escritas por el usuario -que no tienen vector
precomputado- la app cae a recuperacion lexica. Esa frontera queda declarada en
el propio asset (`modo_consulta_libre`) para que el reporte no confunda ambos
regimenes.

Salidas (en el directorio de assets de la app):
    curriculo_collao.json   fragmentos + embeddings + vocabulario
    consultas_eval.json     100 consultas + embeddings + respuesta dorada

Uso:
    python scripts/fase2_exportar_assets_android.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag.indice_vectorial import (  # noqa: E402
    PREFIJO_CONSULTA,
    TOP_K_POR_DEFECTO,
    UMBRAL_COBERTURA_LEXICA,
    UMBRAL_POR_DEFECTO,
    IndiceVectorial,
)

INDICE = ROOT / "data" / "processed" / "indice_vectorial"
EVAL = ROOT / "data" / "eval" / "100_consultas_minedu.jsonl"

ASSETS = (
    ROOT.parent
    / "repos-externos/gallery/Android/src/app/src/main/assets/tesis"
)

CANDIDATOS_EMBED = [
    ROOT / "modelos" / "embeddings" / "multilingual-e5-small",
    ROOT.parent / "modelos" / "embeddings" / "multilingual-e5-small",
]

# 5 decimales bastan: los vectores estan normalizados y la diferencia de
# coseno frente a float32 pleno queda por debajo de 1e-4.
DECIMALES = 5

_RE_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def resolver_embed() -> Path:
    for c in CANDIDATOS_EMBED:
        if (c / "config.json").exists():
            return c
    raise FileNotFoundError("No se encontro multilingual-e5-small")


def redondear(vector: np.ndarray) -> list[float]:
    return [round(float(x), DECIMALES) for x in vector]


def main() -> None:
    ap = argparse.ArgumentParser(description="Exporta assets RAG para Android")
    ap.add_argument("--destino", default=str(ASSETS))
    args = ap.parse_args()

    if not INDICE.exists():
        raise SystemExit(f"Falta {INDICE}. Ejecuta scripts/fase2_construir_indice.py")
    if not EVAL.exists():
        raise SystemExit(f"Falta {EVAL}. Ejecuta scripts/fase1_generar_eval.py")

    destino = Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)

    ruta_embed = resolver_embed()
    indice = IndiceVectorial.cargar(INDICE, ruta_embed)
    print(f"[assets] fragmentos : {len(indice.fragmentos)}")
    print(f"[assets] dimension  : {indice.matriz.shape[1]}")

    # --- corpus curricular ------------------------------------------------
    fragmentos = []
    for f, vector in zip(indice.fragmentos, indice.matriz):
        fragmentos.append(
            {
                "chunkId": f.get("chunk_id", ""),
                "titulo": f.get("titulo", ""),
                "area": f.get("area", ""),
                "grado": f.get("grado", ""),
                "contenidoEs": f.get("contenido_es", ""),
                "contenidoQu": f.get("contenido_qu", ""),
                "referencia": f.get("referencia", ""),
                "origen": f.get("origen", ""),
                "palabrasClaveQu": f.get("palabras_clave_qu") or [],
                "palabrasClaveEs": f.get("palabras_clave_es") or [],
                "embedding": redondear(vector),
            }
        )

    corpus = {
        "version": 1,
        "modeloEmbeddings": ruta_embed.name,
        "dimension": int(indice.matriz.shape[1]),
        "metrica": "coseno (producto punto sobre vectores normalizados)",
        "topK": TOP_K_POR_DEFECTO,
        "umbralCoseno": UMBRAL_POR_DEFECTO,
        "umbralCoberturaLexica": UMBRAL_COBERTURA_LEXICA,
        "modoConsultaLibre": (
            "Las consultas sin vector precomputado se resuelven por recuperacion "
            "lexica sobre el mismo corpus; no usan coseno."
        ),
        "vocabulario": sorted(indice._vocabulario),
        "fragmentos": fragmentos,
    }

    ruta_corpus = destino / "curriculo_collao.json"
    ruta_corpus.write_text(
        json.dumps(corpus, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    print(f"[assets] -> {ruta_corpus.name}  "
          f"({ruta_corpus.stat().st_size / 1024:.0f} KB)")

    # --- consultas de evaluacion ------------------------------------------
    items = [
        json.loads(l) for l in EVAL.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    textos = [PREFIJO_CONSULTA + i["consulta"] for i in items]
    vectores = indice._modelo.encode(
        textos, batch_size=16, convert_to_numpy=True,
        normalize_embeddings=True, show_progress_bar=False,
    ).astype(np.float32)

    consultas = []
    for item, vector in zip(items, vectores):
        consultas.append(
            {
                "id": item["id"],
                "consulta": item["consulta"],
                "idioma": item["idioma"],
                "tipo": item["tipo"],
                "procedencia": item["procedencia"],
                "respondeConCorpus": item.get("responde_con_corpus", True),
                "respuestaDorada": item.get("respuesta_dorada", ""),
                "respuestaDoradaQu": item.get("respuesta_dorada_qu", ""),
                "chunkEsperado": item.get("chunk_esperado", ""),
                "embedding": redondear(vector),
            }
        )

    ruta_eval = destino / "consultas_eval.json"
    ruta_eval.write_text(
        json.dumps(
            {"version": 1, "n": len(consultas), "consultas": consultas},
            ensure_ascii=False, separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    print(f"[assets] -> {ruta_eval.name}  "
          f"({ruta_eval.stat().st_size / 1024:.0f} KB)")

    # --- verificacion -----------------------------------------------------
    print("\n[assets] verificacion de coseno con vectores exportados")
    matriz = np.array([f["embedding"] for f in fragmentos], dtype=np.float32)
    for consulta in consultas[:3]:
        v = np.array(consulta["embedding"], dtype=np.float32)
        sims = matriz @ v
        mejor = int(np.argmax(sims))
        print(f"  {consulta['consulta'][:52]:52s} -> "
              f"{fragmentos[mejor]['chunkId']:24s} {sims[mejor]:.4f}")


if __name__ == "__main__":
    main()
