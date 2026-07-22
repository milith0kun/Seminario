from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIGURACIONES = ROOT / "configuraciones"
DATOS = ROOT / "datos"
MODELOS = ROOT / "modelos"
EXPERIMENTOS = ROOT / "experimentos"
REPORTES = ROOT / "reportes"
SRC = ROOT / "src"

# Alias de compatibilidad
CONFIGS = CONFIGURACIONES
DATA = DATOS
MODELS = MODELOS
EXPERIMENTS = EXPERIMENTOS
REPORTS = REPORTES


def cargar_yaml(nombre: str) -> dict:
    import yaml

    path = CONFIGURACIONES / nombre
    if not path.exists() and (CONFIGURACIONES / f"{nombre}.yaml").exists():
        path = CONFIGURACIONES / f"{nombre}.yaml"
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_yaml(name: str) -> dict:
    return cargar_yaml(name)

