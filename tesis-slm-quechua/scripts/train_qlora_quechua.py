"""FASE 3 - Adaptacion QLoRA de Qwen2.5-3B-Instruct a Quechua Collao / EIB.

Configuracion del plan de tesis:
    cuantizacion 4-bit NF4 con doble cuantizacion, computo en bfloat16/float16
    r=16, alpha=32, dropout=0.05
    target_modules = q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj
    learning rate 2e-4, scheduler coseno, optimizador paged AdamW de 8 bits

Restriccion de hardware: la GPU disponible tiene 4 GB de VRAM, muy por debajo
de lo habitual para un modelo de 3B. Los ajustes por defecto (longitud 384,
batch 1, acumulacion 8, gradient checkpointing) estan elegidos para caber en
ese presupuesto. Con `--sin-cuantizar` se puede entrenar en CPU, pero a esa
escala el tiempo es prohibitivo y solo sirve como prueba de humo.

Uso:
    python scripts/train_qlora_quechua.py --epocas 1 --max-pasos 500
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DATASET = ROOT / "data" / "train" / "dataset_qlora.jsonl"
SALIDA = ROOT / "modelos" / "adaptadores" / "qlora_quechua_collao"

CANDIDATOS_BASE = [
    ROOT / "modelos" / "base" / "Qwen2.5-3B-Instruct",
    ROOT.parent / "modelos" / "base" / "Qwen2.5-3B-Instruct",
]

TARGET_MODULES = [
    "q_proj", "k_proj", "v_proj", "o_proj",
    "gate_proj", "up_proj", "down_proj",
]


def resolver_base() -> Path:
    for c in CANDIDATOS_BASE:
        if (c / "config.json").exists():
            return c
    raise FileNotFoundError(
        "No se encontro Qwen2.5-3B-Instruct en: "
        + ", ".join(str(c) for c in CANDIDATOS_BASE)
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Entrenamiento QLoRA Quechua Collao")
    ap.add_argument("--epocas", type=float, default=1.0)
    ap.add_argument("--max-pasos", type=int, default=-1)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--r", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--dropout", type=float, default=0.05)
    ap.add_argument("--longitud", type=int, default=384)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--acumulacion", type=int, default=8)
    ap.add_argument("--sin-cuantizar", action="store_true",
                    help="Entrena sin 4-bit (CPU o GPU con VRAM suficiente)")
    ap.add_argument("--limite-ejemplos", type=int, default=None)
    args = ap.parse_args()

    import torch
    from datasets import Dataset
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        DataCollatorForLanguageModeling,
        Trainer,
        TrainingArguments,
    )

    if not DATASET.exists():
        raise SystemExit(
            f"Falta {DATASET}. Ejecuta scripts/fase3_construir_dataset_qlora.py"
        )

    ruta_base = resolver_base()
    hay_cuda = torch.cuda.is_available()
    cuantizar = not args.sin_cuantizar and hay_cuda

    print(f"[qlora] modelo base : {ruta_base}")
    print(f"[qlora] CUDA        : {hay_cuda}")
    if hay_cuda:
        props = torch.cuda.get_device_properties(0)
        print(f"[qlora] GPU         : {props.name} ({props.total_memory/1e9:.1f} GB)")
    print(f"[qlora] cuantizacion: {'4-bit NF4' if cuantizar else 'desactivada'}")

    if not hay_cuda and not args.sin_cuantizar:
        raise SystemExit(
            "QLoRA en 4-bit requiere CUDA y bitsandbytes. Instala un torch con "
            "soporte CUDA, o usa --sin-cuantizar para una prueba en CPU."
        )

    # --- datos -----------------------------------------------------------
    registros = [
        json.loads(l) for l in DATASET.read_text(encoding="utf-8").splitlines() if l.strip()
    ]
    if args.limite_ejemplos:
        registros = registros[: args.limite_ejemplos]
    print(f"[qlora] ejemplos    : {len(registros)}")

    tokenizador = AutoTokenizer.from_pretrained(str(ruta_base), trust_remote_code=True)
    if tokenizador.pad_token is None:
        tokenizador.pad_token = tokenizador.eos_token

    def formatear(registro: dict) -> dict:
        texto = tokenizador.apply_chat_template(
            registro["mensajes"], tokenize=False, add_generation_prompt=False
        )
        return {"text": texto}

    ds = Dataset.from_list(registros).map(
        formatear, remove_columns=["mensajes", "tarea", "fuente", "id"]
    )

    def tokenizar(lote: dict) -> dict:
        return tokenizador(
            lote["text"],
            truncation=True,
            max_length=args.longitud,
            padding=False,
        )

    ds = ds.map(tokenizar, batched=True, remove_columns=["text"])

    # --- modelo ----------------------------------------------------------
    kwargs = {"trust_remote_code": True}
    if cuantizar:
        from transformers import BitsAndBytesConfig

        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.float16,
        )
        kwargs["device_map"] = {"": 0}
    else:
        kwargs["dtype"] = torch.float32

    modelo = AutoModelForCausalLM.from_pretrained(str(ruta_base), **kwargs)
    modelo.config.use_cache = False  # incompatible con gradient checkpointing

    if cuantizar:
        modelo = prepare_model_for_kbit_training(
            modelo, use_gradient_checkpointing=True
        )

    config_lora = LoraConfig(
        r=args.r,
        lora_alpha=args.alpha,
        lora_dropout=args.dropout,
        target_modules=TARGET_MODULES,
        bias="none",
        task_type="CAUSAL_LM",
    )
    modelo = get_peft_model(modelo, config_lora)
    modelo.print_trainable_parameters()

    # --- entrenamiento ---------------------------------------------------
    argumentos = TrainingArguments(
        output_dir=str(SALIDA / "checkpoints"),
        num_train_epochs=args.epocas,
        max_steps=args.max_pasos,
        per_device_train_batch_size=args.batch,
        gradient_accumulation_steps=args.acumulacion,
        gradient_checkpointing=True,
        learning_rate=args.lr,
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        logging_steps=10,
        save_steps=200,
        save_total_limit=2,
        fp16=cuantizar,
        optim="paged_adamw_8bit" if cuantizar else "adamw_torch",
        report_to=[],
        seed=42,
    )

    entrenador = Trainer(
        model=modelo,
        args=argumentos,
        train_dataset=ds,
        data_collator=DataCollatorForLanguageModeling(tokenizador, mlm=False),
    )

    print("[qlora] iniciando entrenamiento...")
    resultado = entrenador.train()

    SALIDA.mkdir(parents=True, exist_ok=True)
    modelo.save_pretrained(str(SALIDA))
    tokenizador.save_pretrained(str(SALIDA))

    (SALIDA / "entrenamiento_meta.json").write_text(
        json.dumps(
            {
                "modelo_base": str(ruta_base),
                "n_ejemplos": len(registros),
                "cuantizacion": "4-bit NF4" if cuantizar else "ninguna",
                "r": args.r,
                "alpha": args.alpha,
                "dropout": args.dropout,
                "target_modules": TARGET_MODULES,
                "learning_rate": args.lr,
                "longitud_maxima": args.longitud,
                "batch": args.batch,
                "acumulacion": args.acumulacion,
                "metricas": {k: float(v) for k, v in resultado.metrics.items()},
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[qlora] adaptador -> {SALIDA.relative_to(ROOT)}")
    print(f"[qlora] loss final : {resultado.metrics.get('train_loss', float('nan')):.4f}")


if __name__ == "__main__":
    main()
