from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from rank_bm25 import BM25Okapi


def tokenize(text: str) -> list[str]:
    return re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9']+", text.lower())


class BM25Index:
    def __init__(self, chunks: list[dict[str, Any]]) -> None:
        self.chunks = chunks
        self.corpus = [tokenize(c.get("text", "")) for c in chunks]
        self.bm25 = BM25Okapi(self.corpus) if chunks else None

    @classmethod
    def from_jsonl(cls, path: Path) -> "BM25Index":
        chunks = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    chunks.append(json.loads(line))
        return cls(chunks)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        if not self.bm25 or not self.chunks:
            return []
        scores = self.bm25.get_scores(tokenize(query))
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]
        out = []
        for idx, score in ranked:
            item = dict(self.chunks[idx])
            item["score"] = float(score)
            out.append(item)
        return out


IndiceBM25 = BM25Index
tokenizar = tokenize

