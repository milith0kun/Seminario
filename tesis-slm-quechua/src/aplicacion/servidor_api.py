from __future__ import annotations

import json
import socket
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comun.rutas import DATOS, MODELOS  # noqa: E402
from src.inferencia.ejecutor_modelo import ModelRunner  # noqa: E402
from src.inferencia.enrutador_lenguaje import detect_language  # noqa: E402
from src.rag.constructor_contexto import build_context  # noqa: E402
from src.rag.indice_bm25 import BM25Index  # noqa: E402

app = FastAPI(
    title="Servidor API SLM + RAG Quechua Collao",
    description="Backend API para chat bilingüe, conmutación E1-E4 y recolección de telemetría.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Estado global lazy
runner: ModelRunner | None = None
retriever: BM25Index | None = None
NEXT_OUT_DIR = ROOT / "apps" / "pwa" / "out"


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def init_services() -> None:
    global runner, retriever
    if runner is None:
        runner = ModelRunner()
    if retriever is None:
        chunks_path = DATOS / "corpus_rag" / "chunks.jsonl"
        if chunks_path.exists():
            retriever = BM25Index.from_jsonl(chunks_path)


class ChatRequest(BaseModel):
    pregunta: str = Field(..., description="Consulta del estudiante o docente")
    modo: str = Field("E4_rag_reglas", description="Modo: E1_base, E2_rag, E3_reglas, E4_rag_reglas")
    idioma: str = Field("auto", description="Idioma forzado o 'auto'")


class TelemetriaRequest(BaseModel):
    id_interaccion: str = Field(..., description="UUID único de la interacción")
    pregunta: str
    respuesta: str
    modo: str
    valoracion: str = Field(..., description="like o dislike")
    correccion_usuario: str | None = None


@app.on_event("startup")
def startup_event():
    init_services()


@app.get("/api/estado")
def obtener_estado() -> dict[str, Any]:
    init_services()
    chunks_cnt = len(retriever.chunks) if retriever else 0
    model_exists = runner.model_path.exists() if runner else False
    return {
        "estado": "ok",
        "ip_local": get_local_ip(),
        "puerto": 8000,
        "modelo_cargado": model_exists,
        "modelo_path": str(runner.model_path) if runner else "",
        "chunks_rag": chunks_cnt,
        "modos_disponibles": ["E1_base", "E2_rag", "E3_reglas", "E4_rag_reglas"],
    }


@app.post("/api/chat")
def procesar_chat(req: ChatRequest) -> dict[str, Any]:
    init_services()
    if not req.pregunta.strip():
        raise HTTPException(status_code=400, detail="La pregunta no puede estar vacía.")

    modo = req.modo.lower()
    if modo not in {"e1_base", "e2_rag", "e3_reglas", "e4_rag_reglas"}:
        modo = "e4_rag_reglas"

    lang = req.idioma if req.idioma in {"es", "qu_collao", "mixed_es_qu"} else detect_language(req.pregunta)
    use_rag = modo in {"e2_rag", "e4_rag_reglas"}
    use_rules = modo in {"e3_reglas", "e4_rag_reglas"}

    context = None
    hits_info = []
    if use_rag and retriever:
        hits = retriever.search(req.pregunta, top_k=3)
        context = build_context(hits, max_chunks=3)
        for h in hits:
            hits_info.append(
                {
                    "source_id": h.get("source_id"),
                    "title": h.get("title", ""),
                    "score": h.get("score", 0.0),
                    "text": h.get("text", "")[:120] + "...",
                }
            )

    # Inferencia con modelo local
    result = runner.generate(req.pregunta, context=context, language=lang)
    if result.error:
        raise HTTPException(status_code=500, detail=f"Error en inferencia del modelo: {result.error}")

    interaccion_id = str(uuid.uuid4())
    return {
        "id_interaccion": interaccion_id,
        "respuesta": result.text,
        "modo": modo,
        "idioma_detectado": lang,
        "contexto_rag": hits_info,
        "latencia_ms": result.latency_ms,
        "tokens_per_s": result.tokens_per_s,
        "backend": result.backend,
    }


@app.post("/api/telemetria")
def guardar_telemetria(req: TelemetriaRequest) -> dict[str, Any]:
    out_dir = DATOS / "entrenamiento"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "telemetria_interacciones.jsonl"

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "id_interaccion": req.id_interaccion,
        "pregunta": req.pregunta,
        "respuesta": req.respuesta,
        "modo": req.modo,
        "valoracion": req.valoracion,
        "correccion_usuario": req.correccion_usuario,
    }

    with out_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return {"status": "ok", "mensaje": "Retroalimentación guardada correctamente."}


# Servir la interfaz Next.js exportada estáticamente
if NEXT_OUT_DIR.exists():
    app.mount("/_next", StaticFiles(directory=str(NEXT_OUT_DIR / "_next")), name="next_static")

    @app.get("/")
    def servir_interfaz_next():
        index_file = NEXT_OUT_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return HTMLResponse("<h1>Next.js PWA Build (apps/pwa/out) no encontrado. Ejecuta 'npm run build' en apps/pwa</h1>")
