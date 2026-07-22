from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.comun.rutas import ROOT, cargar_yaml
from src.inferencia.plantillas_prompt import build_messages


@dataclass
class GenerationResult:
    text: str
    latency_ms: float
    backend: str
    model_path: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    tokens_per_s: float | None = None
    error: str | None = None


class ModelRunner:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or cargar_yaml("modelos.yaml")
        self.cfg = self.config["inference_offline"]
        self.model_path = ROOT / self.cfg["local_path"]
        self._llm = None

    def ensure_model(self) -> Path:
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado: {self.model_path}. "
                "Ejecuta: python scripts/descargar_modelo.py"
            )
        return self.model_path

    def _load(self):
        if self._llm is not None:
            return self._llm

        from llama_cpp import Llama

        self.ensure_model()
        self._llm = Llama(
            model_path=str(self.model_path),
            n_ctx=int(self.cfg.get("n_ctx", 2048)),
            n_gpu_layers=int(self.cfg.get("n_gpu_layers", 0)),
            n_threads=int(self.cfg.get("n_threads", 4)),
            chat_format=self.cfg.get("chat_format", "qwen"),
            verbose=False,
        )
        return self._llm

    def generate(
        self,
        user_text: str,
        context: str | None = None,
        language: str = "es",
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> GenerationResult:
        started = time.perf_counter()
        try:
            llm = self._load()
            messages = build_messages(user_text, context=context, language=language)
            out = llm.create_chat_completion(
                messages=messages,
                max_tokens=int(max_tokens or self.cfg.get("max_tokens", 256)),
                temperature=float(temperature if temperature is not None else self.cfg.get("temperature", 0.2)),
            )
            choice = out["choices"][0]["message"]["content"]
            usage = out.get("usage") or {}
            latency_ms = (time.perf_counter() - started) * 1000
            completion = usage.get("completion_tokens")
            tps = None
            if completion and latency_ms > 0:
                tps = completion / (latency_ms / 1000)
            return GenerationResult(
                text=(choice or "").strip(),
                latency_ms=latency_ms,
                backend="llama_cpp",
                model_path=str(self.model_path),
                prompt_tokens=usage.get("prompt_tokens"),
                completion_tokens=completion,
                tokens_per_s=tps,
            )
        except Exception as exc:  # noqa: BLE001
            latency_ms = (time.perf_counter() - started) * 1000
            return GenerationResult(
                text="",
                latency_ms=latency_ms,
                backend="llama_cpp",
                model_path=str(self.model_path),
                error=str(exc),
            )


EjecutorModelo = ModelRunner

