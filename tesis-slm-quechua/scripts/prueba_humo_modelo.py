from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comun.rutas import REPORTES, cargar_yaml  # noqa: E402
from src.inferencia.enrutador_lenguaje import detect_language  # noqa: E402
from src.inferencia.ejecutor_modelo import ModelRunner  # noqa: E402


def main() -> int:
    cfg = cargar_yaml("modelos.yaml")
    prompt = cfg["smoke_test"]["prompt"]
    max_tokens = int(cfg["smoke_test"]["max_tokens"])

    runner = ModelRunner(cfg)
    lang = detect_language(prompt)
    print(f"[lang] {lang}")
    print(f"[prompt] {prompt}")
    print("[run] generando...")

    result = runner.generate(prompt, language=lang, max_tokens=max_tokens)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "language": lang,
        "text": result.text,
        "latency_ms": result.latency_ms,
        "tokens_per_s": result.tokens_per_s,
        "prompt_tokens": result.prompt_tokens,
        "completion_tokens": result.completion_tokens,
        "backend": result.backend,
        "model_path": result.model_path,
        "error": result.error,
    }

    out_dir = REPORTES / "pruebas_humo"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "smoke_model.json"
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


    if result.error:
        print(f"[error] {result.error}")
        print(f"[log] {out_path}")
        return 1

    print(f"[ok] {result.latency_ms:.0f} ms | tps={result.tokens_per_s}")
    print(f"[answer]\n{result.text}")
    print(f"[log] {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
