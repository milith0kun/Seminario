from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comun.rutas import DATOS  # noqa: E402


def descargar_americasnlp(target_dir: Path) -> Path:
    import subprocess

    target_dir.mkdir(parents=True, exist_ok=True)
    repo_dir = target_dir / "americasnlp2021"
    if (repo_dir / ".git").exists() or (repo_dir / "README.md").exists():
        print(f"[skip] AmericasNLP2021 ya existe en: {repo_dir}")
        return repo_dir

    print(f"[download] Clonando AmericasNLP2021 desde GitHub en: {repo_dir}")
    cmd = [
        "git",
        "clone",
        "--depth",
        "1",
        "https://github.com/AmericasNLP/americasnlp2021.git",
        str(repo_dir),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[ok] AmericasNLP2021 clonado correctamente.")
    else:
        print(f"[warn] Falló git clone AmericasNLP: {res.stderr}")
    return repo_dir


def descargar_llamacha(target_dir: Path) -> Path:
    from datasets import load_dataset

    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / "llamacha_monolingual_quechua.jsonl"
    if out_file.exists():
        print(f"[skip] Dataset Llamacha ya existe en: {out_file}")
        return out_file

    print(f"[download] Cargando dataset 'Llamacha/monolingual-quechua-iic' desde Hugging Face...")
    ds = load_dataset("Llamacha/monolingual-quechua-iic")
    print(f"[ok] Dataset Llamacha cargado. Guardando copia local en {out_file}...")

    # Guardar en jsonl local para uso sin conexion
    import json

    total = 0
    with out_file.open("w", encoding="utf-8") as f:
        split_keys = list(ds.keys())
        for split in split_keys:
            for row in ds[split]:
                rec = {"split": split, **dict(row)}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                total += 1
    print(f"[ok] Guardados {total} registros monolingües quechua en {out_file}.")
    return out_file


def main() -> None:
    external_dir = DATOS / "crudos" / "external"
    external_dir.mkdir(parents=True, exist_ok=True)

    print("=== DESCARGA DE DATASETS EXTERNOS (AmericasNLP & Llamacha) ===")
    descargar_americasnlp(external_dir)
    descargar_llamacha(external_dir)
    print("\n[done] Procesos de descarga finalizados.")


if __name__ == "__main__":
    main()
