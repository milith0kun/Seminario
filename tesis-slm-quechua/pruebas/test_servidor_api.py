from __future__ import annotations

import json
from pathlib import Path
from fastapi.testclient import TestClient

from src.aplicacion.servidor_api import app
from src.comun.rutas import DATOS

client = TestClient(app)


def test_obtener_estado():
    res = client.get("/api/estado")
    assert res.status_code == 200
    data = res.json()
    assert data["estado"] == "ok"
    assert "E4_rag_reglas" in data["modos_disponibles"]


def test_telemetria_endpoint():
    payload = {
        "id_interaccion": "test-uuid-1234",
        "pregunta": "Prueba telemetria",
        "respuesta": "Respuesta prueba",
        "modo": "E4_rag_reglas",
        "valoracion": "like",
        "correccion_usuario": "Corrección de prueba",
    }
    res = client.post("/api/telemetria", json=payload)
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    out_file = DATOS / "entrenamiento" / "telemetria_interacciones.jsonl"
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "test-uuid-1234" in content
