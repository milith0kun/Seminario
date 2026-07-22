from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comun.rutas import cargar_yaml  # noqa: E402


def download_gguf(force: bool = False) -> Path:
    from huggingface_hub import hf_hub_download

    cfg = cargar_yaml("modelos.yaml")["inference_offline"]

    target = ROOT / cfg["local_path"]
    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not force:
        print(f"[ok] Ya existe: {target}")
        return target

    print(f"[download] {cfg['gguf_repo']} :: {cfg['gguf_file']}")
    path = hf_hub_download(
        repo_id=cfg["gguf_repo"],
        filename=cfg["gguf_file"],
        local_dir=str(target.parent),
    )
    downloaded = Path(path)
    if downloaded.resolve() != target.resolve():
        if target.exists():
            target.unlink()
        downloaded.replace(target)
    print(f"[ok] Guardado en: {target}")
    print(f"[size] {target.stat().st_size / (1024 ** 3):.2f} GB")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga GGUF Qwen2.5-3B Q4_K_M")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    download_gguf(force=args.force)


if __name__ == "__main__":
    main()
