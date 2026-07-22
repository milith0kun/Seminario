from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comun.rutas import DATOS, EXPERIMENTOS  # noqa: E402
from src.inferencia.enrutador_lenguaje import detect_language  # noqa: E402
from src.inferencia.ejecutor_modelo import ModelRunner  # noqa: E402


def main() -> None:
    limit = 5
    if "--all" in sys.argv:
        limit = 10**9
    for arg in sys.argv:
        if arg.startswith("--limit="):
            limit = int(arg.split("=", 1)[1])

    qpath = DATOS / "evaluacion" / "questions_seed.csv"
    if not qpath.exists():
        qpath = DATOS / "eval" / "questions_seed.csv"
    rows = list(csv.DictReader(qpath.open(encoding="utf-8")))[:limit]
    runner = ModelRunner()

    out_dir = EXPERIMENTOS / "E1_base" / "salidas"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"ejecucion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"


    print(f"[E1] {len(rows)} preguntas -> {out_path}")
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            q = row["question"]
            lang = row.get("language") or detect_language(q)
            result = runner.generate(q, language=lang)
            rec = {
                "id": row["id"],
                "question": q,
                "language": lang,
                "answer": result.text,
                "latency_ms": result.latency_ms,
                "tokens_per_s": result.tokens_per_s,
                "error": result.error,
                "config": "E1_base",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            status = "ERR" if result.error else "OK"
            print(f"  [{status}] {row['id']} {result.latency_ms:.0f}ms")
    print("[done]")


if __name__ == "__main__":
    main()
