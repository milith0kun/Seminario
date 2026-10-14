"""FASE 4 - Benchmark comparativo de los escenarios E1, E2 y E3.

  E1  Control zero-shot. Modelo base, RAG desactivado.
  E2  Modelo base + recuperacion vectorial curricular (coseno, top-k).
  E3  Modelo adaptado + recuperacion vectorial + andamiaje pedagogico EIB.

E3 usa el adaptador QLoRA si esta disponible; si no lo esta, se ejecuta sobre
el modelo base y el informe lo declara explicitamente, porque en ese caso la
diferencia frente a E2 mide el efecto del prompt de andamiaje y no el del
entrenamiento.

Uso:
    python scripts/evaluar_escenarios.py --escenarios E1,E2,E3 \
        --output results/benchmark_100_eval.json [--limite N]
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluacion import metricas as M  # noqa: E402
from src.rag.indice_vectorial import IndiceVectorial  # noqa: E402

DATA = ROOT / "data"
EVAL = DATA / "eval" / "100_consultas_minedu.jsonl"
INDICE = DATA / "processed" / "indice_vectorial"
ADAPTADOR_QLORA = ROOT / "modelos" / "adaptadores" / "qlora_quechua_collao"

CANDIDATOS_GGUF = [
    ROOT / "modelos" / "gguf" / "qwen2.5-3b-instruct-q4_k_m.gguf",
    ROOT.parent / "modelos" / "gguf" / "qwen2.5-3b-instruct-q4_k_m.gguf",
]
CANDIDATOS_EMBED = [
    ROOT / "modelos" / "embeddings" / "multilingual-e5-small",
    ROOT.parent / "modelos" / "embeddings" / "multilingual-e5-small",
]

TOP_K = 3
UMBRAL_COSENO = 0.65
MAX_TOKENS = 192
TEMPERATURA = 0.2

SISTEMA_BASE = (
    "Eres un asistente pedagogico bilingue (Quechua Collao - Castellano) para "
    "Educacion Intercultural Bilingue en el Peru. Responde de forma breve, clara "
    "y adecuada al nivel de primaria."
)

SISTEMA_E3 = (
    "Eres un tutor escolar bilingue (Quechua Collao - Castellano) de Educacion "
    "Intercultural Bilingue. Estructura cada respuesta con andamiaje pedagogico: "
    "1) pregunta orientadora que active saberes previos, 2) pistas en quechua y "
    "castellano, 3) explicacion fundamentada en el material curricular, "
    "4) ejemplo del entorno andino. Se breve en cada paso."
)

INSTRUCCION_SIN_RESPALDO = (
    "No se recupero material curricular para esta consulta. Si no dispones de la "
    "informacion, indicalo explicitamente en lugar de suponer datos."
)


@dataclass
class Respuesta:
    texto: str = ""
    ttft_ms: float = 0.0
    latencia_ms: float = 0.0
    tokens: int = 0
    throughput: float = 0.0
    error: str | None = None


@dataclass
class Escenario:
    codigo: str
    nombre: str
    usa_rag: bool
    sistema: str
    usa_adaptador: bool = False
    notas: list[str] = field(default_factory=list)


ESCENARIOS = {
    "E1": Escenario("E1", "Control zero-shot (sin RAG)", False, SISTEMA_BASE),
    "E2": Escenario("E2", "SLM base + RAG curricular", True, SISTEMA_BASE),
    "E3": Escenario("E3", "SLM adaptado + RAG + andamiaje EIB", True, SISTEMA_E3,
                    usa_adaptador=True),
}


def resolver(candidatos: list[Path], que: str) -> Path:
    for c in candidatos:
        if c.exists():
            return c
    raise FileNotFoundError(f"No se encontro {que}: " + ", ".join(map(str, candidatos)))


def ram_pico_mb() -> float:
    try:
        import psutil

        return psutil.Process().memory_info().rss / (1024 * 1024)
    except ImportError:
        return 0.0


class MotorLlama:
    """Envoltorio de llama.cpp con medicion de TTFT por streaming."""

    def __init__(self, ruta_gguf: Path, n_ctx: int = 2048, n_threads: int | None = None):
        from llama_cpp import Llama

        import os

        self.ruta = ruta_gguf
        self.llm = Llama(
            model_path=str(ruta_gguf),
            n_ctx=n_ctx,
            n_threads=n_threads or max(1, (os.cpu_count() or 4) // 2),
            n_gpu_layers=0,
            verbose=False,
        )

    def generar(self, sistema: str, usuario: str, max_tokens: int = MAX_TOKENS) -> Respuesta:
        mensajes = [
            {"role": "system", "content": sistema},
            {"role": "user", "content": usuario},
        ]
        inicio = time.perf_counter()
        ttft = 0.0
        piezas: list[str] = []
        try:
            flujo = self.llm.create_chat_completion(
                messages=mensajes,
                max_tokens=max_tokens,
                temperature=TEMPERATURA,
                stream=True,
            )
            for trozo in flujo:
                delta = trozo["choices"][0].get("delta", {})
                contenido = delta.get("content")
                if not contenido:
                    continue
                if ttft == 0.0:
                    # Primer token util: define el TTFT reportado en la tesis.
                    ttft = (time.perf_counter() - inicio) * 1000
                piezas.append(contenido)
        except Exception as exc:  # noqa: BLE001
            return Respuesta(
                error=str(exc), latencia_ms=(time.perf_counter() - inicio) * 1000
            )

        texto = "".join(piezas).strip()
        latencia = (time.perf_counter() - inicio) * 1000
        n_tokens = len(self.llm.tokenize(texto.encode("utf-8"))) if texto else 0
        decodificacion_s = max((latencia - ttft) / 1000, 1e-6)
        return Respuesta(
            texto=texto,
            ttft_ms=ttft,
            latencia_ms=latencia,
            tokens=n_tokens,
            throughput=n_tokens / decodificacion_s if n_tokens else 0.0,
        )


def construir_prompt(escenario: Escenario, consulta: str, recuperacion) -> tuple[str, list[str]]:
    """Devuelve el prompt de usuario y los contextos inyectados."""
    if not escenario.usa_rag:
        return consulta, []

    if recuperacion is None or not recuperacion.hubo_recuperacion:
        return f"{INSTRUCCION_SIN_RESPALDO}\n\nConsulta: {consulta}", []

    contextos = [f.texto_para_contexto() for f in recuperacion.fragmentos]
    bloques = []
    for i, frag in enumerate(recuperacion.fragmentos, start=1):
        bloques.append(
            f"[Fuente {i} | {frag.titulo} | {frag.referencia} | "
            f"similitud={frag.similitud:.3f}]\n{frag.texto_para_contexto()}"
        )
    contexto = "\n\n".join(bloques)
    prompt = (
        "MATERIAL CURRICULAR RECUPERADO:\n"
        f"{contexto}\n\n"
        "Responde a la consulta fundamentandote unicamente en el material "
        "anterior. Si el material no cubre la consulta, indicalo.\n\n"
        f"Consulta: {consulta}"
    )
    return prompt, contextos


def evaluar_item(item: dict, respuesta: Respuesta, contextos: list[str],
                 codificador, recuperacion) -> dict:
    texto = respuesta.texto
    referencia = item.get("respuesta_dorada", "")
    es_sonda = not item.get("responde_con_corpus", True)

    ling = {
        "chrf_pp": M.chrf_pp(texto, referencia),
        "bleu4": M.bleu4(texto, referencia),
        "rouge_l": M.rouge_l(texto, referencia),
        "similitud_coseno": 0.0,
    }

    relevancia = 0.0
    if texto and codificador is not None:
        vectores = codificador.encode(
            [f"query: {item['consulta']}", f"passage: {texto}", f"passage: {referencia}"],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        relevancia = M.answer_relevance(vectores[0], vectores[1])
        ling["similitud_coseno"] = M.similitud_coseno(vectores[1], vectores[2])

    fund = {
        "faithfulness": M.faithfulness(texto, contextos),
        "answer_relevance": relevancia,
        "cobertura_contexto": M.cobertura_contexto(texto, contextos),
    }

    abstiene = M.es_abstencion(texto)
    return {
        "id": item["id"],
        "consulta": item["consulta"],
        "idioma": item["idioma"],
        "tipo": item["tipo"],
        "procedencia": item["procedencia"],
        "es_sonda_alucinacion": es_sonda,
        "respuesta": texto,
        "error": respuesta.error,
        "linguisticas": ling,
        "fundamentacion": fund,
        "eficiencia": {
            "ttft_ms": respuesta.ttft_ms,
            "latencia_total_ms": respuesta.latencia_ms,
            "throughput_tok_s": respuesta.throughput,
            "tokens_generados": respuesta.tokens,
            "ram_pico_mb": ram_pico_mb(),
        },
        "recuperacion": {
            "n_fragmentos": len(contextos),
            "similitud_maxima": getattr(recuperacion, "similitud_maxima", 0.0),
            "cobertura_lexica": getattr(recuperacion, "cobertura_lexica", 0.0),
            "sin_respaldo": getattr(recuperacion, "sin_respaldo", False),
            "chunks": [f.chunk_id for f in getattr(recuperacion, "fragmentos", [])],
        },
        "alucinacion": {
            "se_abstuvo": abstiene,
            "invento_entidad": M.inventa_entidad(texto),
            # En una sonda la respuesta correcta es abstenerse.
            "correcto": abstiene if es_sonda else not M.inventa_entidad(texto),
        },
    }


def promediar(items: list[dict]) -> dict:
    """Agrega los resultados de un escenario."""
    if not items:
        return {}

    def media(ruta: tuple[str, str], filtro=None) -> float:
        vals = [
            i[ruta[0]][ruta[1]]
            for i in items
            if (filtro is None or filtro(i)) and i.get("error") is None
        ]
        return float(np.mean(vals)) if vals else 0.0

    con_corpus = lambda i: not i["es_sonda_alucinacion"]  # noqa: E731
    sondas = [i for i in items if i["es_sonda_alucinacion"]]
    con_rag = [i for i in items if i["recuperacion"]["n_fragmentos"] > 0]

    return {
        "n_items": len(items),
        "n_errores": sum(1 for i in items if i.get("error")),
        "linguisticas": {
            "chrf_pp": media(("linguisticas", "chrf_pp"), con_corpus),
            "bleu4": media(("linguisticas", "bleu4"), con_corpus),
            "rouge_l": media(("linguisticas", "rouge_l"), con_corpus),
            "similitud_coseno": media(("linguisticas", "similitud_coseno"), con_corpus),
        },
        "fundamentacion": {
            # Solo tiene sentido sobre items donde hubo contexto inyectado.
            "faithfulness": float(
                np.mean([i["fundamentacion"]["faithfulness"] for i in con_rag])
            ) if con_rag else 0.0,
            "answer_relevance": media(("fundamentacion", "answer_relevance")),
            "cobertura_contexto": float(
                np.mean([i["fundamentacion"]["cobertura_contexto"] for i in con_rag])
            ) if con_rag else 0.0,
            "items_con_contexto": len(con_rag),
        },
        "eficiencia": {
            "ttft_ms_medio": media(("eficiencia", "ttft_ms")),
            "throughput_tok_s_medio": media(("eficiencia", "throughput_tok_s")),
            "latencia_total_ms_media": media(("eficiencia", "latencia_total_ms")),
            "ram_pico_mb": max((i["eficiencia"]["ram_pico_mb"] for i in items), default=0.0),
        },
        "alucinacion": {
            "n_sondas": len(sondas),
            "abstenciones_correctas": sum(1 for i in sondas if i["alucinacion"]["se_abstuvo"]),
            "tasa_abstencion_correcta": (
                sum(1 for i in sondas if i["alucinacion"]["se_abstuvo"]) / len(sondas)
            ) if sondas else 0.0,
            "entidades_inventadas_en_sondas": sum(
                1 for i in sondas if i["alucinacion"]["invento_entidad"]
            ),
            "tasa_invencion_global": sum(
                1 for i in items if i["alucinacion"]["invento_entidad"]
            ) / len(items),
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark de escenarios E1/E2/E3")
    ap.add_argument("--escenarios", default="E1,E2,E3")
    ap.add_argument("--output", default="results/benchmark_100_eval.json")
    ap.add_argument("--limite", type=int, default=None,
                    help="Evalua solo las primeras N consultas (pruebas rapidas)")
    ap.add_argument("--max-tokens", type=int, default=MAX_TOKENS)
    args = ap.parse_args()

    codigos = [c.strip().upper() for c in args.escenarios.split(",") if c.strip()]
    desconocidos = [c for c in codigos if c not in ESCENARIOS]
    if desconocidos:
        raise SystemExit(f"Escenarios desconocidos: {desconocidos}")

    if not EVAL.exists():
        raise SystemExit(f"Falta {EVAL}. Ejecuta scripts/fase1_generar_eval.py")
    if not INDICE.exists():
        raise SystemExit(f"Falta {INDICE}. Ejecuta scripts/fase2_construir_indice.py")

    items = [json.loads(l) for l in EVAL.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.limite:
        items = items[: args.limite]

    ruta_gguf = resolver(CANDIDATOS_GGUF, "modelo GGUF")
    ruta_embed = resolver(CANDIDATOS_EMBED, "modelo de embeddings")

    print(f"[eval] consultas   : {len(items)}")
    print(f"[eval] escenarios  : {', '.join(codigos)}")
    print(f"[eval] modelo      : {ruta_gguf.name}")

    indice = IndiceVectorial.cargar(INDICE, ruta_embed)
    codificador = indice._modelo  # reutiliza el encoder ya cargado
    print(f"[eval] indice      : {len(indice.fragmentos)} fragmentos\n")

    hay_adaptador = ADAPTADOR_QLORA.exists()
    if not hay_adaptador and "E3" in codigos:
        ESCENARIOS["E3"].notas.append(
            "Adaptador QLoRA no encontrado en modelos/adaptadores/qlora_quechua_collao. "
            "E3 se ejecuto sobre el modelo BASE: la diferencia frente a E2 mide el "
            "efecto del prompt de andamiaje, NO el del entrenamiento."
        )
        ESCENARIOS["E3"].usa_adaptador = False

    print("[eval] cargando modelo en memoria...")
    motor = MotorLlama(ruta_gguf)
    print("[eval] modelo cargado\n")

    salida = Path(args.output)
    if not salida.is_absolute():
        salida = ROOT / salida
    salida.parent.mkdir(parents=True, exist_ok=True)

    reporte = {
        "metadatos": {
            "fecha": datetime.now(timezone.utc).isoformat(),
            "modelo_generacion": ruta_gguf.name,
            "modelo_embeddings": ruta_embed.name,
            "adaptador_qlora_disponible": hay_adaptador,
            "n_consultas": len(items),
            "top_k": TOP_K,
            "umbral_coseno": UMBRAL_COSENO,
            "max_tokens": args.max_tokens,
            "temperatura": TEMPERATURA,
            "plataforma": f"{platform.system()} {platform.release()} / {platform.machine()}",
            "backend": "llama.cpp (CPU)",
        },
        "escenarios": {},
    }

    for codigo in codigos:
        esc = ESCENARIOS[codigo]
        print(f"=== {codigo}: {esc.nombre} ===")
        if esc.notas:
            for n in esc.notas:
                print(f"    AVISO: {n}")

        resultados: list[dict] = []
        inicio = time.perf_counter()
        for n, item in enumerate(items, start=1):
            recuperacion = None
            if esc.usa_rag:
                recuperacion = indice.recuperar(
                    item["consulta"], top_k=TOP_K, umbral=UMBRAL_COSENO
                )
            prompt, contextos = construir_prompt(esc, item["consulta"], recuperacion)
            respuesta = motor.generar(esc.sistema, prompt, max_tokens=args.max_tokens)
            resultados.append(
                evaluar_item(item, respuesta, contextos, codificador, recuperacion)
            )

            if n % 10 == 0 or n == len(items):
                transcurrido = time.perf_counter() - inicio
                print(f"    {n:3d}/{len(items)}  "
                      f"{transcurrido/60:.1f} min  "
                      f"({transcurrido/n:.1f} s/consulta)")
                # Checkpoint: una corrida larga no debe perderse por una caida.
                reporte["escenarios"][codigo] = {
                    "nombre": esc.nombre,
                    "usa_rag": esc.usa_rag,
                    "usa_adaptador_qlora": esc.usa_adaptador,
                    "notas": esc.notas,
                    "resumen": promediar(resultados),
                    "items": resultados,
                }
                salida.write_text(
                    json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8"
                )

        resumen = promediar(resultados)
        reporte["escenarios"][codigo] = {
            "nombre": esc.nombre,
            "usa_rag": esc.usa_rag,
            "usa_adaptador_qlora": esc.usa_adaptador,
            "notas": esc.notas,
            "resumen": resumen,
            "items": resultados,
        }
        salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding="utf-8")

        L, F, E, A = (resumen["linguisticas"], resumen["fundamentacion"],
                      resumen["eficiencia"], resumen["alucinacion"])
        print(f"    chrF++={L['chrf_pp']:.2f}  BLEU-4={L['bleu4']:.2f}  "
              f"ROUGE-L={L['rouge_l']:.2f}  coseno={L['similitud_coseno']:.3f}")
        print(f"    faithfulness={F['faithfulness']:.3f}  "
              f"relevance={F['answer_relevance']:.3f}")
        print(f"    TTFT={E['ttft_ms_medio']:.0f} ms  "
              f"{E['throughput_tok_s_medio']:.2f} tok/s  RAM={E['ram_pico_mb']:.0f} MB")
        print(f"    abstencion correcta en sondas="
              f"{A['abstenciones_correctas']}/{A['n_sondas']}\n")

    print(f"[eval] reporte -> {salida.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
