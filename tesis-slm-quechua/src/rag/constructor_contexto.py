from __future__ import annotations

from typing import Any


def build_context(chunks: list[dict[str, Any]], max_chunks: int = 5) -> str:
    parts = []
    for i, c in enumerate(chunks[:max_chunks], start=1):
        sid = c.get("source_id", "?")
        ref = c.get("source_ref", "")
        text = c.get("text", "").strip()
        parts.append(f"[{i}] source={sid} ref={ref}\n{text}")
    return "\n\n".join(parts)


construir_contexto = build_context

