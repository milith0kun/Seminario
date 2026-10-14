"""FASE 4 (on-device) - Metricas sobre el barrido ejecutado en el dispositivo.

Toma el JSON que produce la pantalla de evaluacion de la app -donde la
inferencia corre sobre LiteRT en Android- y calcula las metricas del plan de
tesis. Las cifras de eficiencia (TTFT, throughput, RAM) vienen medidas por el
propio dispositivo; aqui solo se agregan.

Entrada:  results/benchmark_ondevice.json  (extraido con adb pull)
Salidas:  results/metricas_ondevice.json
          reportes/comparativa_ondevice.md

Uso:
    python scripts/fase4_metricas_ondevice.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.evaluacion import metricas as M  # noqa: E402

ORDEN = ["E1", "E2", "E3"]

CANDIDATOS_EMBED = [
    ROOT / "modelos" / "embeddings" / "multilingual-e5-small",
    ROOT.parent / "modelos" / "embeddings" / "multilingual-e5-small",
]

_SUFIJOS_QUECHUA = re.compile(
    r"\w+(kuna|nchik|manta|paq|wan|pi|ta|qa|mi|chu|nki|nku|spa|sqa|yuq|niyuq)\b",
    re.IGNORECASE,
)
_RE_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def responde_en_quechua(texto: str, umbral: float = 0.15) -> bool:
    palabras = _RE_PALABRA.findall(texto or "")
    if len(palabras) < 3:
        return False
    return len(_SUFIJOS_QUECHUA.findall(texto)) / len(palabras) > umbral


def cargar_codificador():
    for c in CANDIDATOS_EMBED:
        if (c / "config.json").exists():
            from sentence_transformers import SentenceTransformer

            return SentenceTransformer(str(c), device="cpu")
    return None


def contextos_de(item: dict, corpus: dict[str, dict]) -> list[str]:
    """Reconstruye el texto de los fragmentos que la app inyecto."""
    textos = []
    for cid in item.get("chunksRecuperados", []):
        frag = corpus.get(cid)
        if not frag:
            continue
        partes = []
        if frag.get("contenidoEs"):
            partes.append(frag["contenidoEs"])
        if frag.get("contenidoQu"):
            partes.append(frag["contenidoQu"])
        if partes:
            textos.append("\n".join(partes))
    return textos


def evaluar(items: list[dict], corpus: dict[str, dict], codificador) -> list[dict]:
    salida = []
    for item in items:
        texto = item.get("respuesta", "") or ""
        referencia = item.get("respuestaDorada", "") or ""
        contextos = contextos_de(item, corpus)

        ling = {
            "chrf_pp": M.chrf_pp(texto, referencia),
            "bleu4": M.bleu4(texto, referencia),
            "rouge_l": M.rouge_l(texto, referencia),
            "similitud_coseno": 0.0,
        }
        relevancia = 0.0
        if texto and codificador is not None:
            vs = codificador.encode(
                [f"query: {item['consulta']}", f"passage: {texto}",
                 f"passage: {referencia}"],
                convert_to_numpy=True, normalize_embeddings=True,
                show_progress_bar=False,
            )
            relevancia = M.answer_relevance(vs[0], vs[1])
            ling["similitud_coseno"] = M.similitud_coseno(vs[1], vs[2])

        abstiene = M.es_abstencion(texto)
        es_sonda = bool(item.get("esSondaAlucinacion"))

        salida.append(
            {
                **item,
                "linguisticas": ling,
                "fundamentacion": {
                    "faithfulness": M.faithfulness(texto, contextos),
                    "answer_relevance": relevancia,
                    "cobertura_contexto": M.cobertura_contexto(texto, contextos),
                },
                "alucinacion": {
                    "se_abstuvo": abstiene,
                    "invento_entidad": M.inventa_entidad(texto),
                    "correcto": abstiene if es_sonda else not M.inventa_entidad(texto),
                },
                "responde_en_quechua": responde_en_quechua(texto),
            }
        )
    return salida


def resumir(items: list[dict]) -> dict:
    if not items:
        return {}
    validos = [i for i in items if not i.get("error")]
    con_corpus = [i for i in validos if not i["esSondaAlucinacion"]]
    con_rag = [i for i in validos if i.get("nFragmentos", 0) > 0]
    sondas = [i for i in validos if i["esSondaAlucinacion"]]

    def media(xs):
        return float(np.mean(xs)) if xs else 0.0

    return {
        "n_items": len(items),
        "n_errores": sum(1 for i in items if i.get("error")),
        "linguisticas": {
            k: media([i["linguisticas"][k] for i in con_corpus])
            for k in ("chrf_pp", "bleu4", "rouge_l", "similitud_coseno")
        },
        "fundamentacion": {
            "faithfulness": media([i["fundamentacion"]["faithfulness"] for i in con_rag]),
            "answer_relevance": media(
                [i["fundamentacion"]["answer_relevance"] for i in validos]),
            "cobertura_contexto": media(
                [i["fundamentacion"]["cobertura_contexto"] for i in con_rag]),
            "items_con_contexto": len(con_rag),
        },
        "eficiencia": {
            "ttft_ms_medio": media([i["ttftMs"] for i in validos]),
            "ttft_ms_mediana": float(np.median([i["ttftMs"] for i in validos])) if validos else 0.0,
            # Solo promedia los items con ventana de decodificacion medible:
            # incluir los ceros hundiria la media sin significado fisico.
            "throughput_tok_s_medio": media(
                [i["throughputTokS"] for i in validos if i.get("throughputTokS", 0) > 0]),
            "n_con_throughput_medible": sum(
                1 for i in validos if i.get("throughputTokS", 0) > 0),
            "throughput_efectivo_tok_s_medio": media(
                [i.get("throughputEfectivoTokS", 0.0) for i in validos]),
            "longitud_respuesta_chars_media": media(
                [len(i.get("respuesta", "")) for i in validos]),
            "latencia_total_ms_media": media([i["latenciaTotalMs"] for i in validos]),
            "ram_pss_mb_max": max((i["ramPssMb"] for i in validos), default=0),
            "ram_pss_mb_media": media([i["ramPssMb"] for i in validos]),
            "latencia_recuperacion_ms_media": media(
                [i["latenciaRecuperacionMs"] for i in con_rag]),
        },
        "alucinacion": {
            "n_sondas": len(sondas),
            "abstenciones_correctas": sum(1 for i in sondas if i["alucinacion"]["se_abstuvo"]),
            "tasa_abstencion_correcta": (
                sum(1 for i in sondas if i["alucinacion"]["se_abstuvo"]) / len(sondas)
            ) if sondas else 0.0,
            "entidades_inventadas_en_sondas": sum(
                1 for i in sondas if i["alucinacion"]["invento_entidad"]),
            "tasa_invencion_global": (
                sum(1 for i in validos if i["alucinacion"]["invento_entidad"]) / len(validos)
            ) if validos else 0.0,
        },
        "recuperacion": {
            "modo": (con_rag[0].get("modoRecuperacion") if con_rag else "sin_rag"),
            "similitud_maxima_media": media([i["similitudMaxima"] for i in con_rag]),
            "sin_respaldo": sum(1 for i in validos if i.get("sinRespaldo")),
        },
        "deriva_idioma": {
            "consultas_quechua": sum(1 for i in con_corpus if i["idioma"] == "qu_collao"),
            "respuestas_quechua": sum(
                1 for i in con_corpus if i["idioma"] == "qu_collao" and i["responde_en_quechua"]),
        },
    }


def tabla(cab: list[str], filas: list[list[str]]) -> str:
    out = ["| " + " | ".join(cab) + " |",
           "|" + "|".join([" --- "] * len(cab)) + "|"]
    out += ["| " + " | ".join(f) + " |" for f in filas]
    return "\n".join(out)


def construir_reporte(meta: dict, resumenes: dict, items: list[dict]) -> str:
    presentes = [c for c in ORDEN if c in resumenes]
    base = resumenes[presentes[0]]
    o: list[str] = []

    o.append("# Comparativa experimental on-device — E1 / E2 / E3")
    o.append("")
    o.append("Barrido ejecutado **dentro de la aplicacion Android**, sobre el "
             "runtime LiteRT que despliega la tesis. Todas las cifras de "
             "eficiencia proceden del dispositivo.")
    o.append("")

    o.append("## 1. Entorno de ejecucion")
    o.append("")
    o.append(tabla(["Parametro", "Valor"], [
        ["Dispositivo", meta.get("dispositivo", "")],
        ["ABI", meta.get("abi", "")],
        ["Android", meta.get("androidRelease", "")],
        ["RAM total", f"{meta.get('ramTotalMb', 0)} MB"],
        ["Runtime", meta.get("runtime", "")],
        ["Modelo", f"`{meta.get('modelo', '')}`"],
        ["Acelerador", meta.get("acelerador", "")],
        ["Longitud de contexto", str(meta.get("longitudContexto", ""))],
        ["Consultas", str(meta.get("nConsultas", ""))],
        ["Fragmentos del corpus", str(meta.get("fragmentosCorpus", ""))],
        ["Recuperacion", f"coseno, top-k={meta.get('topK')}, "
                         f"umbral={meta.get('umbralCoseno')}"],
    ]))
    o.append("")

    o.append("## 2. Calidad linguistica y semantica")
    o.append("")
    filas = []
    for c in presentes:
        L, Lb = resumenes[c]["linguisticas"], base["linguisticas"]
        def d(k, dec=2):
            v = L[k] - Lb[k]
            return f"{L[k]:.{dec}f} ({'+' if v >= 0 else ''}{v:.{dec}f})"
        filas.append([f"**{c}**", d("chrf_pp"), d("bleu4"), d("rouge_l"),
                      d("similitud_coseno", 3)])
    o.append(tabla(["Escenario", "chrF++", "BLEU-4", "ROUGE-L", "Coseno"], filas))
    o.append("")
    o.append(f"Diferencia frente a **{presentes[0]}** entre parentesis. "
             "Las sondas de alucinacion se excluyen: su respuesta correcta es "
             "una abstencion, no un parafraseo.")
    o.append("")

    o.append("## 3. Fundamentacion")
    o.append("")
    filas = [[f"**{c}**",
              f"{resumenes[c]['fundamentacion']['faithfulness']:.3f}",
              f"{resumenes[c]['fundamentacion']['answer_relevance']:.3f}",
              f"{resumenes[c]['fundamentacion']['cobertura_contexto']:.3f}",
              str(resumenes[c]["fundamentacion"]["items_con_contexto"])]
             for c in presentes]
    o.append(tabla(["Escenario", "Faithfulness", "Answer relevance",
                    "Cobertura de contexto", "Items con contexto"], filas))
    o.append("")
    o.append("> Aproximaciones locales deterministas, no los estimadores de "
             "RAGAS (que exigen un LLM juez por API).")
    o.append("")

    o.append("## 4. Alucinacion")
    o.append("")
    filas = [[f"**{c}**",
              f"{resumenes[c]['alucinacion']['abstenciones_correctas']}/"
              f"{resumenes[c]['alucinacion']['n_sondas']}",
              f"{100 * resumenes[c]['alucinacion']['tasa_abstencion_correcta']:.1f} %",
              str(resumenes[c]["alucinacion"]["entidades_inventadas_en_sondas"]),
              f"{100 * resumenes[c]['alucinacion']['tasa_invencion_global']:.1f} %"]
             for c in presentes]
    o.append(tabla(["Escenario", "Abstenciones correctas", "Tasa",
                    "Entidades inventadas", "Invencion global"], filas))
    o.append("")

    o.append("## 5. Eficiencia on-device")
    o.append("")
    filas = []
    for c in presentes:
        E = resumenes[c]["eficiencia"]
        filas.append([f"**{c}**",
                      f"{E['ttft_ms_medio']:.0f}",
                      f"{E['ttft_ms_mediana']:.0f}",
                      f"{E['throughput_tok_s_medio']:.2f}",
                      f"{E['latencia_total_ms_media']:.0f}",
                      f"{E['ram_pss_mb_max']:.0f}"])
    o.append(tabla(["Escenario", "TTFT medio (ms)", "TTFT mediana (ms)",
                    "Throughput decode (tok/s)", "Latencia total (ms)",
                    "RAM PSS pico (MB)"], filas))
    o.append("")
    o.append("")
    filas = []
    for c in presentes:
        E = resumenes[c]["eficiencia"]
        filas.append([f"**{c}**",
                      f"{E.get('throughput_efectivo_tok_s_medio', 0):.2f}",
                      str(E.get("n_con_throughput_medible", 0)),
                      f"{E.get('longitud_respuesta_chars_media', 0):.0f}"])
    o.append(tabla(["Escenario", "Throughput efectivo (tok/s)",
                    "Items con decode medible", "Longitud media (chars)"], filas))
    o.append("")
    o.append("> Medido por la propia app sobre el runtime LiteRT del "
             "dispositivo. El *throughput decode* solo promedia los items cuya "
             "ventana posterior al primer token supera los 100 ms; el "
             "*efectivo* se calcula extremo a extremo e incluye el prefill. El "
             "conteo de tokens es una estimacion por palabras y signos: el "
             "runtime no expone el tokenizador a este nivel.")
    o.append("")
    o.append("La longitud media de respuesta es un control de sanidad: valores "
             "de pocos caracteres indican que el modelo dejo de generar y que "
             "la corrida no es valida, aunque el JSON se haya escrito sin "
             "errores.")
    o.append("")

    o.append("## 6. Coste de la recuperacion")
    o.append("")
    filas = [[f"**{c}**",
              resumenes[c]["recuperacion"]["modo"],
              f"{resumenes[c]['recuperacion']['similitud_maxima_media']:.3f}",
              f"{resumenes[c]['eficiencia']['latencia_recuperacion_ms_media']:.1f}",
              str(resumenes[c]["recuperacion"]["sin_respaldo"])]
             for c in presentes]
    o.append(tabla(["Escenario", "Modo", "Similitud maxima media",
                    "Latencia de recuperacion (ms)", "Consultas sin respaldo"], filas))
    o.append("")

    o.append("## 7. chrF++ por idioma de la consulta")
    o.append("")
    por_idioma: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for i in items:
        if i["esSondaAlucinacion"] or i.get("error"):
            continue
        por_idioma[i["idioma"]][i["escenario"]].append(i["linguisticas"]["chrf_pp"])
    filas = []
    for idioma in sorted(por_idioma):
        fila = [f"`{idioma}`"]
        n = 0
        for c in presentes:
            vals = por_idioma[idioma][c]
            n = max(n, len(vals))
            fila.append(f"{np.mean(vals):.2f}" if vals else "-")
        fila.append(str(n))
        filas.append(fila)
    o.append(tabla(["Idioma"] + presentes + ["n"], filas))
    o.append("")

    o.append("## 8. Deriva de idioma")
    o.append("")
    filas = []
    for c in presentes:
        D = resumenes[c]["deriva_idioma"]
        tasa = D["respuestas_quechua"] / D["consultas_quechua"] if D["consultas_quechua"] else 0.0
        filas.append([f"**{c}**", str(D["consultas_quechua"]),
                      str(D["respuestas_quechua"]), f"{100 * tasa:.1f} %"])
    o.append(tabla(["Escenario", "Consultas en quechua",
                    "Respuestas en quechua", "Tasa"], filas))
    o.append("")
    o.append("Fraccion de consultas en Quechua Collao que el modelo respondio "
             "efectivamente en quechua, por densidad de sufijos aglutinantes. "
             "Una caida de chrF++ puede deberse a un cambio de lengua y no a "
             "una perdida de contenido.")
    o.append("")

    return "\n".join(o)


def main() -> None:
    ap = argparse.ArgumentParser(description="Metricas del barrido on-device")
    ap.add_argument("--input", default="results/benchmark_ondevice.json")
    ap.add_argument("--output", default="results/metricas_ondevice.json")
    ap.add_argument("--reporte", default="reportes/comparativa_ondevice.md")
    ap.add_argument("--corpus", default=None,
                    help="Asset curriculo_collao.json (para reconstruir contextos)")
    ap.add_argument("--combinar", action="store_true",
                    help="Une los results/benchmark_ondevice_E*.json de las "
                         "corridas por escenario")
    args = ap.parse_args()

    if args.combinar:
        # Cada escenario corre en su propio proceso, asi que llega en un archivo
        # aparte. Los metadatos son equivalentes entre corridas salvo la lista de
        # escenarios, que se reconstruye a partir de lo realmente medido.
        partes = sorted((ROOT / "results").glob("benchmark_ondevice_E*.json"))
        if not partes:
            raise SystemExit(
                "No hay archivos results/benchmark_ondevice_E*.json.\n"
                "Ejecuta antes: powershell -File scripts/ejecutar_barrido_ondevice.ps1"
            )
        resultados = []
        meta = None
        for parte in partes:
            d = json.loads(parte.read_text(encoding="utf-8"))
            if meta is None:
                meta = dict(d["metadatos"])
            resultados.extend(d["resultados"])
            print(f"[ondevice] {parte.name}: {len(d['resultados'])} mediciones")
        meta["escenarios"] = sorted({r["escenario"] for r in resultados})
    else:
        entrada = Path(args.input)
        if not entrada.is_absolute():
            entrada = ROOT / entrada
        if not entrada.exists():
            raise SystemExit(
                f"No existe {entrada}.\n"
                "Ejecuta el barrido con:\n"
                "  powershell -File scripts/ejecutar_barrido_ondevice.ps1\n"
                "y luego combina los resultados con --combinar"
            )
        datos = json.loads(entrada.read_text(encoding="utf-8"))
        meta = datos["metadatos"]
        resultados = datos["resultados"]
    print(f"[ondevice] mediciones : {len(resultados)}")
    print(f"[ondevice] dispositivo: {meta.get('dispositivo')} / {meta.get('abi')}")

    ruta_corpus = Path(args.corpus) if args.corpus else (
        ROOT.parent
        / "repos-externos/gallery/Android/src/app/src/main/assets/tesis/curriculo_collao.json"
    )
    corpus: dict[str, dict] = {}
    if ruta_corpus.exists():
        for f in json.loads(ruta_corpus.read_text(encoding="utf-8"))["fragmentos"]:
            corpus[f["chunkId"]] = f
        print(f"[ondevice] corpus     : {len(corpus)} fragmentos")

    print("[ondevice] calculando metricas...")
    codificador = cargar_codificador()
    items = evaluar(resultados, corpus, codificador)

    resumenes = {}
    for codigo in ORDEN:
        del_escenario = [i for i in items if i["escenario"] == codigo]
        if del_escenario:
            resumenes[codigo] = resumir(del_escenario)

    salida = Path(args.output)
    if not salida.is_absolute():
        salida = ROOT / salida
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps({"metadatos": meta, "resumenes": resumenes, "items": items},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    reporte = Path(args.reporte)
    if not reporte.is_absolute():
        reporte = ROOT / reporte
    reporte.parent.mkdir(parents=True, exist_ok=True)
    reporte.write_text(construir_reporte(meta, resumenes, items), encoding="utf-8")

    print()
    for c, r in resumenes.items():
        L, E, A = r["linguisticas"], r["eficiencia"], r["alucinacion"]
        print(f"  {c}: chrF++={L['chrf_pp']:6.2f}  "
              f"faith={r['fundamentacion']['faithfulness']:.3f}  "
              f"TTFT={E['ttft_ms_medio']:7.0f}ms  "
              f"{E['throughput_tok_s_medio']:5.2f} tok/s  "
              f"RAM={E['ram_pss_mb_max']:4.0f}MB  "
              f"abst={A['abstenciones_correctas']}/{A['n_sondas']}  "
              f"err={r['n_errores']}")
    print()
    print(f"[ondevice] -> {salida.relative_to(ROOT)}")
    print(f"[ondevice] -> {reporte.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
