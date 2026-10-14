"""FASE 2 - Construccion del indice vectorial curricular.

Codifica los fragmentos de data/processed/corpus_curricular.jsonl con
multilingual-e5-small y persiste el indice en data/processed/indice_vectorial/.

Uso:
    python scripts/fase2_construir_indice.py [--probar]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.rag.indice_vectorial import (  # noqa: E402
    TOP_K_POR_DEFECTO,
    UMBRAL_POR_DEFECTO,
    IndiceVectorial,
)

CORPUS = ROOT / "data" / "processed" / "corpus_curricular.jsonl"
DESTINO = ROOT / "data" / "processed" / "indice_vectorial"

# El modelo se busca primero dentro del proyecto y luego en la raiz del repo.
CANDIDATOS_MODELO = [
    ROOT / "modelos" / "embeddings" / "multilingual-e5-small",
    ROOT.parent / "modelos" / "embeddings" / "multilingual-e5-small",
]

CONSULTAS_PRUEBA = [
    "Que es la fotosintesis?",
    "Como se organiza el trabajo comunal en el ayllu?",
    "Yakuq Muyuynin imataq chay?",
    "Cual es el codigo de la Resolucion Ministerial de Robotica Educativa EIB?",
]


def resolver_modelo() -> Path:
    for ruta in CANDIDATOS_MODELO:
        if (ruta / "config.json").exists():
            return ruta
    raise FileNotFoundError(
        "No se encontro multilingual-e5-small en: "
        + ", ".join(str(c) for c in CANDIDATOS_MODELO)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Fase 2: indice vectorial curricular")
    ap.add_argument("--probar", action="store_true",
                    help="Ejecuta consultas de verificacion tras construir el indice")
    ap.add_argument("--top-k", type=int, default=TOP_K_POR_DEFECTO)
    ap.add_argument("--umbral", type=float, default=UMBRAL_POR_DEFECTO)
    args = ap.parse_args()

    if not CORPUS.exists():
        raise SystemExit(
            f"Falta {CORPUS}. Ejecuta antes: python scripts/fase1_curar_datos.py"
        )

    fragmentos = [
        json.loads(l) for l in CORPUS.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    ruta_modelo = resolver_modelo()

    print(f"[fase2] fragmentos      : {len(fragmentos)}")
    print(f"[fase2] modelo          : {ruta_modelo.name}")
    print("[fase2] codificando pasajes...")

    indice = IndiceVectorial.construir(fragmentos, ruta_modelo)
    indice.guardar(DESTINO)

    print(f"[fase2] dimension       : {indice.matriz.shape[1]}")
    print(f"[fase2] indice guardado : {DESTINO.relative_to(ROOT)}")

    if args.probar:
        print(f"\n[fase2] verificacion (top_k={args.top_k}, umbral={args.umbral})")
        for consulta in CONSULTAS_PRUEBA:
            r = indice.recuperar(consulta, top_k=args.top_k, umbral=args.umbral)
            print(f"\n  > {consulta}")
            print(f"    sim_max={r.similitud_maxima:.3f}  "
                  f"recuperados={len(r.fragmentos)}  {r.latencia_ms:.1f} ms")
            for f in r.fragmentos:
                print(f"      [{f.similitud:.3f}] {f.chunk_id:24s} {f.titulo[:52]}")
            if r.bajo_umbral:
                print("      (ningun fragmento supera el umbral: consulta sin respaldo)")


if __name__ == "__main__":
    main()
