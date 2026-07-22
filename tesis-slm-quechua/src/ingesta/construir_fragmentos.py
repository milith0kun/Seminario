from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comun.rutas import DATOS, cargar_yaml  # noqa: E402
from src.ingesta.fragmentar_documentos import chunk_glossary_line, chunk_prose, write_jsonl  # noqa: E402
from src.ingesta.limpiar_texto import clean_text  # noqa: E402


def main() -> None:
    rag_cfg = cargar_yaml("rag.yaml")["chunking"]
    manifest = DATOS / "manifiesto.csv"
    if not manifest.exists():
        manifest = DATOS / "manifest.csv"
    if not manifest.exists():
        raise SystemExit(f"Falta {manifest}")

    chunks = []
    with manifest.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    for row in rows:
        if str(row.get("use_in_rag", "")).lower() != "true":
            continue
        path = ROOT / row["path"]
        if not path.exists():
            print(f"[skip] no existe: {path}")
            continue
        text = clean_text(path.read_text(encoding="utf-8"))
        meta = {
            "language": row.get("language", "es"),
            "dialect": row.get("dialect", "collao"),
            "domain": row.get("domain", "na"),
            "grade": row.get("grade", "na"),
            "source_ref": row.get("title", row["id"]),
            "title": row.get("title", ""),
        }
        source_type = row.get("source_type", "txt")
        if source_type in {"glossary", "glosario"} or "glosario" in row["id"]:
            n = 0
            for line in text.splitlines():
                n += 1
                item = chunk_glossary_line(line, row["id"], meta, n)
                if item:
                    chunks.append(item)
        else:
            chunks.extend(
                chunk_prose(
                    text,
                    row["id"],
                    meta,
                    min_tokens=int(rag_cfg["prose_tokens_min"]),
                    max_tokens=int(rag_cfg["prose_tokens_max"]),
                    overlap_tokens=int(rag_cfg["overlap_tokens"]),
                )
            )

    out = DATOS / "corpus_rag" / "chunks.jsonl"
    write_jsonl(chunks, out)
    print(f"[ok] {len(chunks)} chunks -> {out}")



if __name__ == "__main__":
    main()
