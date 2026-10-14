"""FASE 3.2 - Fusion de los adaptadores QLoRA y exportacion del modelo adaptado.

Etapa 1 (portable): fusiona las matrices LoRA sobre los pesos base y guarda el
modelo resultante en formato HuggingFace safetensors.

Etapa 2 (conversion a .litertlm): requiere el toolchain de Google AI Edge
(`ai-edge-torch`), que a la fecha solo publica ruedas para Linux. En Windows
esta etapa no puede ejecutarse en el mismo entorno; el script lo detecta y
emite las instrucciones exactas en lugar de fallar de forma opaca.

Uso:
    python scripts/fase3_fusionar_y_exportar.py [--gguf] [--salida DIR]
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ADAPTADOR = ROOT / "modelos" / "adaptadores" / "qlora_quechua_collao"
SALIDA_FUSION = ROOT / "modelos" / "fusionados" / "Qwen2.5-3B-Tutor-EIB-Collao"

CANDIDATOS_BASE = [
    ROOT / "modelos" / "base" / "Qwen2.5-3B-Instruct",
    ROOT.parent / "modelos" / "base" / "Qwen2.5-3B-Instruct",
]


def resolver_base() -> Path:
    for c in CANDIDATOS_BASE:
        if (c / "config.json").exists():
            return c
    raise FileNotFoundError("No se encontro el modelo base Qwen2.5-3B-Instruct")


def fusionar(destino: Path) -> Path:
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    ruta_base = resolver_base()
    print(f"[fusion] base      : {ruta_base}")
    print(f"[fusion] adaptador : {ADAPTADOR}")

    # La fusion se hace en float32 sobre CPU: el objetivo es la fidelidad
    # numerica de los pesos resultantes, no la velocidad.
    modelo = AutoModelForCausalLM.from_pretrained(
        str(ruta_base), dtype=torch.float32, device_map="cpu", trust_remote_code=True
    )
    modelo = PeftModel.from_pretrained(modelo, str(ADAPTADOR))
    modelo = modelo.merge_and_unload()

    destino.mkdir(parents=True, exist_ok=True)
    modelo.save_pretrained(str(destino), safe_serialization=True)
    AutoTokenizer.from_pretrained(str(ruta_base), trust_remote_code=True).save_pretrained(
        str(destino)
    )

    meta_adaptador = ADAPTADOR / "entrenamiento_meta.json"
    (destino / "procedencia.json").write_text(
        json.dumps(
            {
                "modelo_base": str(ruta_base),
                "adaptador": str(ADAPTADOR),
                "entrenamiento": (
                    json.loads(meta_adaptador.read_text(encoding="utf-8"))
                    if meta_adaptador.exists() else None
                ),
                "nota": "Pesos con las matrices QLoRA ya fusionadas (merge_and_unload).",
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[fusion] modelo fusionado -> {destino.relative_to(ROOT)}")
    return destino


def exportar_gguf(origen: Path) -> Path | None:
    """Convierte el modelo fusionado a GGUF para evaluarlo con llama.cpp.

    Es la ruta que permite medir E3 con el mismo banco que E1/E2 sin depender
    del toolchain de LiteRT.
    """
    convertidor = None
    for candidato in [
        ROOT / "herramientas" / "llama.cpp" / "convert_hf_to_gguf.py",
        ROOT.parent / "herramientas" / "llama.cpp" / "convert_hf_to_gguf.py",
    ]:
        if candidato.exists():
            convertidor = candidato
            break

    if convertidor is None:
        print("[gguf] convert_hf_to_gguf.py no encontrado.")
        print("       Clona llama.cpp en herramientas/llama.cpp para habilitar "
              "esta conversion:")
        print("       git clone --depth 1 https://github.com/ggml-org/llama.cpp "
              "herramientas/llama.cpp")
        return None

    destino = origen.parent / f"{origen.name}-f16.gguf"
    print(f"[gguf] convirtiendo -> {destino.name}")
    resultado = subprocess.run(
        [sys.executable, str(convertidor), str(origen),
         "--outfile", str(destino), "--outtype", "f16"],
        capture_output=True, text=True,
    )
    if resultado.returncode != 0:
        print("[gguf] la conversion fallo:")
        print(resultado.stderr[-2000:])
        return None
    print(f"[gguf] listo -> {destino}")
    return destino


def instrucciones_litertlm(origen: Path) -> None:
    """Explica como obtener el .litertlm, que no puede generarse en Windows."""
    print()
    print("=" * 72)
    print("CONVERSION A .litertlm (formato de despliegue Android)")
    print("=" * 72)
    if platform.system() == "Windows":
        print("El toolchain de Google AI Edge (`ai-edge-torch`) no publica ruedas")
        print("para Windows. Esta etapa debe ejecutarse en Linux o WSL2:")
    else:
        print("Ejecuta la conversion con el toolchain de Google AI Edge:")
    print()
    print("  # 1. Entorno Linux/WSL2 con Python 3.11")
    print("  pip install ai-edge-torch ai-edge-litert")
    print()
    print("  # 2. Conversion del modelo fusionado")
    print("  python -m ai_edge_torch.generative.examples.qwen.convert_to_tflite \\")
    print(f"      --checkpoint_path {origen} \\")
    print("      --output_path ./salida_litertlm \\")
    print("      --quantize dynamic_int8")
    print()
    print("  # 3. Empaquetado .litertlm y despliegue")
    print("  adb push modelo.litertlm \\")
    print("    /storage/emulated/0/Android/data/com.google.aiedge.gallery/files/"
          "Qwen2_5_3B_Tutor_EIB__E3_Entrenado_/<hash>/")
    print()
    print("Hasta completar ese paso, la entrada 'E3 Entrenado' del catalogo")
    print("Android apunta al MISMO binario que el modelo base.")
    print("=" * 72)


def main() -> None:
    ap = argparse.ArgumentParser(description="Fase 3.2: fusion y exportacion")
    ap.add_argument("--salida", default=str(SALIDA_FUSION))
    ap.add_argument("--gguf", action="store_true",
                    help="Convierte tambien a GGUF para evaluar E3 con llama.cpp")
    args = ap.parse_args()

    if not ADAPTADOR.exists():
        raise SystemExit(
            f"No existe el adaptador {ADAPTADOR}.\n"
            "Ejecuta antes: python scripts/train_qlora_quechua.py"
        )

    destino = Path(args.salida)
    if not destino.is_absolute():
        destino = ROOT / destino

    fusionado = fusionar(destino)
    if args.gguf:
        exportar_gguf(fusionado)
    instrucciones_litertlm(fusionado)


if __name__ == "__main__":
    main()
