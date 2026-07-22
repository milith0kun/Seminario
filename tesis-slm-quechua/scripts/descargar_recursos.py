from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.comun.rutas import cargar_yaml  # noqa: E402


def _size_gb(path: Path) -> float:
    if path.is_file():
        return path.stat().st_size / (1024**3)
    total = 0
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total / (1024**3)


def download_gguf(force: bool = False) -> Path:
    from huggingface_hub import hf_hub_download

    cfg = cargar_yaml("modelos.yaml")["inference_offline"]
    target = ROOT / cfg["local_path"]
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and not force:
        print(f"[skip] GGUF ya existe ({_size_gb(target):.2f} GB): {target}")
        return target
    print(f"[download] GGUF {cfg['gguf_repo']} / {cfg['gguf_file']}")
    path = Path(
        hf_hub_download(
            repo_id=cfg["gguf_repo"],
            filename=cfg["gguf_file"],
            local_dir=str(target.parent),
        )
    )
    if path.resolve() != target.resolve():
        if target.exists():
            target.unlink()
        path.replace(target)
    print(f"[ok] GGUF {_size_gb(target):.2f} GB -> {target}")
    return target


def download_hf_base(force: bool = False) -> Path:
    from huggingface_hub import snapshot_download

    cfg = cargar_yaml("modelos.yaml")["base"]
    target = ROOT / cfg["local_dir"]
    marker = target / "config.json"
    if marker.exists() and not force:
        print(f"[skip] HF base ya existe ({_size_gb(target):.2f} GB): {target}")
        return target
    target.mkdir(parents=True, exist_ok=True)
    print(f"[download] HF base {cfg['hf_id']} (~6 GB, para QLoRA futuro)")
    snapshot_download(
        repo_id=cfg["hf_id"],
        local_dir=str(target),
        ignore_patterns=["*.md", "LICENSE*", "original/*", "*.gguf"],
        max_workers=2,
    )
    print(f"[ok] HF base {_size_gb(target):.2f} GB -> {target}")
    return target


def download_embeddings(force: bool = False) -> Path:
    from huggingface_hub import snapshot_download

    cfg = cargar_yaml("rag.yaml")["embeddings"]
    model_id = cfg["model"]
    target = ROOT / cfg.get(
        "local_dir",
        f"modelos/embeddings/{model_id.replace('/', '__')}",
    )
    marker = target / "config.json"
    weights_ok = (target / "model.safetensors").exists() or (target / "pytorch_model.bin").exists()
    if marker.exists() and weights_ok and not force:
        print(f"[skip] embeddings ya existen ({_size_gb(target):.2f} GB): {target}")
        return target
    target.mkdir(parents=True, exist_ok=True)
    print(f"[download] embeddings {model_id}")
    snapshot_download(
        repo_id=model_id,
        local_dir=str(target),
        ignore_patterns=[
            "onnx/*",
            "openvino/*",
            "*.onnx",
            "rust_model.ot",
            "tf_model.h5",
            "flax_model.msgpack",
        ],
        max_workers=2,
    )
    print(f"[ok] embeddings {_size_gb(target):.2f} GB -> {target}")
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Descarga modelos y recursos locales")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--only",
        choices=["all", "gguf", "hf", "embeddings"],
        default="all",
    )
    args = parser.parse_args()

    if args.only in {"all", "gguf"}:
        download_gguf(force=args.force)
    if args.only in {"all", "embeddings"}:
        download_embeddings(force=args.force)
    if args.only in {"all", "hf"}:
        download_hf_base(force=args.force)
    print("[done]")


if __name__ == "__main__":
    main()
