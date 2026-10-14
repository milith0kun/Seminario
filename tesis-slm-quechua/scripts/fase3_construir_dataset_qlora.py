"""FASE 3.0 - Dataset de entrenamiento para la adaptacion QLoRA.

Combina tres tareas complementarias, todas derivadas de material real del
repositorio (ningun texto quechua se inventa):

  1. modelado_lengua   Continuacion de texto sobre el corpus Collao filtrado.
                       Es la tarea que realmente adapta el modelo a la
                       morfologia aglutinante y al lexico Collao.
  2. normalizacion     Reescritura de texto a ortografia oficial trivocalica
                       (RM 1218-85-ED). El par (crudo -> normalizado) se obtiene
                       del normalizador, no de anotacion manual.
  3. instruccion_eib   Pares pedagogicos con andamiaje bilingue anclados al
                       corpus curricular.

Salida: data/train/dataset_qlora.jsonl  (formato chat de mensajes)

Uso:
    python scripts/fase3_construir_dataset_qlora.py [--max-lm 4000]
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATA = ROOT / "data"
CORPUS_COLLAO = DATA / "processed" / "corpus_collao.jsonl"
PARES = DATA / "train" / "pares_pedagogicos.jsonl"
SALIDA = DATA / "train" / "dataset_qlora.jsonl"

SISTEMA = (
    "Eres un asistente pedagogico bilingue (Quechua Collao - Castellano) para "
    "Educacion Intercultural Bilingue en el Peru."
)

INSTRUCCIONES_LM = [
    "Continua el siguiente texto en Quechua Collao manteniendo el estilo y la morfologia:",
    "Completa de forma coherente este pasaje en Quechua Collao:",
    "Sigue escribiendo en Quechua Collao a partir de este inicio:",
]

INSTRUCCIONES_NORM = [
    "Reescribe el siguiente texto usando la ortografia oficial trivocalica del "
    "quechua (RM 1218-85-ED, vocales a/i/u):",
    "Corrige la ortografia de este texto quechua segun el alfabeto oficial:",
]


def leer_jsonl(ruta: Path) -> list[dict]:
    if not ruta.exists():
        return []
    return [json.loads(l) for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def construir_modelado_lengua(corpus: list[dict], maximo: int, rng: random.Random) -> list[dict]:
    """Divide cada segmento en prefijo/continuacion para entrenar generacion."""
    ejemplos: list[dict] = []
    # Prioriza los segmentos con mas rasgos Collao: son los mas informativos
    # para la adaptacion morfologica.
    candidatos = sorted(
        (s for s in corpus if s["tokens"] >= 12),
        key=lambda s: s["puntaje_collao"],
        reverse=True,
    )[: maximo * 2]
    rng.shuffle(candidatos)

    for seg in candidatos:
        palabras = seg["texto"].split()
        corte = max(4, len(palabras) // 3)
        prefijo, continuacion = " ".join(palabras[:corte]), " ".join(palabras[corte:])
        if len(continuacion.split()) < 4:
            continue
        ejemplos.append(
            {
                "tarea": "modelado_lengua",
                "mensajes": [
                    {"role": "system", "content": SISTEMA},
                    {"role": "user",
                     "content": f"{rng.choice(INSTRUCCIONES_LM)}\n\n{prefijo}"},
                    {"role": "assistant", "content": continuacion},
                ],
                "fuente": seg["fuente"],
            }
        )
        if len(ejemplos) >= maximo:
            break
    return ejemplos


def construir_normalizacion(corpus: list[dict], maximo: int, rng: random.Random) -> list[dict]:
    """Pares (texto original -> texto trivocalico) donde la normalizacion cambio algo."""
    ejemplos: list[dict] = []
    for seg in corpus:
        original, normalizado = seg["texto"], seg["texto_normalizado"]
        if original == normalizado or len(original.split()) < 6:
            continue
        ejemplos.append(
            {
                "tarea": "normalizacion",
                "mensajes": [
                    {"role": "system", "content": SISTEMA},
                    {"role": "user",
                     "content": f"{rng.choice(INSTRUCCIONES_NORM)}\n\n{original}"},
                    {"role": "assistant", "content": normalizado},
                ],
                "fuente": seg["fuente"],
            }
        )
        if len(ejemplos) >= maximo:
            break
    return ejemplos


def construir_instruccion(pares: list[dict]) -> list[dict]:
    ejemplos: list[dict] = []
    for par in pares:
        usuario = par["instruccion"]
        if par.get("entrada"):
            usuario = f"{usuario}\n\n{par['entrada']}"
        ejemplos.append(
            {
                "tarea": "instruccion_eib",
                "mensajes": [
                    {"role": "system", "content": SISTEMA},
                    {"role": "user", "content": usuario},
                    {"role": "assistant", "content": par["respuesta"]},
                ],
                "fuente": par.get("referencia", ""),
            }
        )
    return ejemplos


def main() -> None:
    ap = argparse.ArgumentParser(description="Fase 3.0: dataset QLoRA")
    ap.add_argument("--max-lm", type=int, default=4000)
    ap.add_argument("--max-norm", type=int, default=1500)
    ap.add_argument("--semilla", type=int, default=42)
    args = ap.parse_args()

    rng = random.Random(args.semilla)
    corpus = leer_jsonl(CORPUS_COLLAO)
    pares = leer_jsonl(PARES)
    if not corpus:
        raise SystemExit(f"Falta {CORPUS_COLLAO}. Ejecuta scripts/fase1_curar_datos.py")

    lm = construir_modelado_lengua(corpus, args.max_lm, rng)
    norm = construir_normalizacion(corpus, args.max_norm, rng)
    inst = construir_instruccion(pares)

    # Los ejemplos de instruccion son pocos frente al corpus: se replican para
    # que la senal pedagogica no quede diluida por el modelado de lengua.
    factor = max(1, (len(lm) + len(norm)) // (max(len(inst), 1) * 12))
    inst_ampliado = inst * factor

    dataset = lm + norm + inst_ampliado
    rng.shuffle(dataset)

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8") as f:
        for i, ej in enumerate(dataset):
            ej["id"] = f"tr_{i:06d}"
            f.write(json.dumps(ej, ensure_ascii=False) + "\n")

    print(f"  modelado_lengua : {len(lm)}")
    print(f"  normalizacion   : {len(norm)}")
    print(f"  instruccion_eib : {len(inst)} x{factor} = {len(inst_ampliado)}")
    print(f"  -> {SALIDA.relative_to(ROOT)}  ({len(dataset)} ejemplos)")


if __name__ == "__main__":
    main()
