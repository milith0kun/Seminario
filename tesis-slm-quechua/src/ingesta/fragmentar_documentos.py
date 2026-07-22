from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from src.ingesta.limpiar_texto import clean_text, estimate_tokens


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[\.\!\?])\s+|\n{2,}", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_prose(
    text: str,
    source_id: str,
    meta: dict[str, Any],
    min_tokens: int = 250,
    max_tokens: int = 400,
    overlap_tokens: int = 60,
) -> list[dict[str, Any]]:
    text = clean_text(text)
    sentences = _split_sentences(text)
    chunks: list[dict[str, Any]] = []
    buf: list[str] = []
    buf_tokens = 0
    idx = 0

    def flush() -> None:
        nonlocal buf, buf_tokens, idx
        if not buf:
            return
        body = " ".join(buf).strip()
        if not body:
            buf, buf_tokens = [], 0
            return
        idx += 1
        chunks.append(
            {
                "chunk_id": f"{source_id}_{idx:04d}",
                "source_id": source_id,
                "text": body,
                "tokens_estimated": estimate_tokens(body),
                **meta,
            }
        )
        if overlap_tokens > 0:
            keep: list[str] = []
            keep_tokens = 0
            for s in reversed(buf):
                t = estimate_tokens(s)
                if keep_tokens + t > overlap_tokens and keep:
                    break
                keep.insert(0, s)
                keep_tokens += t
            buf = keep
            buf_tokens = keep_tokens
        else:
            buf, buf_tokens = [], 0

    for sent in sentences:
        t = estimate_tokens(sent)
        if buf_tokens + t > max_tokens and buf_tokens >= min_tokens:
            flush()
        buf.append(sent)
        buf_tokens += t
        if buf_tokens >= max_tokens:
            flush()
    flush()
    return chunks


def chunk_glossary_line(line: str, source_id: str, meta: dict[str, Any], n: int) -> dict[str, Any] | None:
    line = clean_text(line)
    if not line or line.startswith("#"):
        return None
    return {
        "chunk_id": f"{source_id}_{n:04d}",
        "source_id": source_id,
        "text": line,
        "tokens_estimated": estimate_tokens(line),
        **meta,
    }


def write_jsonl(chunks: list[dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")


fragmentar_prosa = chunk_prose
fragmentar_glosario = chunk_glossary_line
escribir_jsonl = write_jsonl

