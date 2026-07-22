from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.inferencia.enrutador_lenguaje import detect_language  # noqa: E402
from src.inferencia.ejecutor_modelo import ModelRunner  # noqa: E402
from src.rag.indice_bm25 import BM25Index  # noqa: E402
from src.rag.constructor_contexto import build_context  # noqa: E402
from src.comun.rutas import DATOS  # noqa: E402


def main() -> None:
    use_rag = "--rag" in sys.argv
    runner = ModelRunner()
    retriever = None
    if use_rag:
        chunks_path = DATOS / "corpus_rag" / "chunks.jsonl"

        if chunks_path.exists():
            retriever = BM25Index.from_jsonl(chunks_path)
            print("[mode] modelo + RAG BM25")
        else:
            print("[warn] no hay chunks; modo solo modelo")
    else:
        print("[mode] solo modelo (E1). Usa --rag para recuperar contexto")

    print("Escribe 'salir' para terminar.\n")
    while True:
        try:
            q = input("tu> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in {"salir", "exit", "quit"}:
            break
        lang = detect_language(q)
        context = None
        if retriever is not None:
            hits = retriever.search(q, top_k=3)
            context = build_context(hits, max_chunks=3)
            print(f"[rag] {len(hits)} chunks | lang={lang}")
        else:
            print(f"[lang] {lang}")
        result = runner.generate(q, context=context, language=lang)
        if result.error:
            print(f"[error] {result.error}")
            continue
        print(f"[bot {result.latency_ms:.0f}ms]\n{result.text}\n")


if __name__ == "__main__":
    main()
