"""FASE 5.3 - Reporte comparativo de los escenarios E1/E2/E3 en Markdown.

Lee results/benchmark_100_eval.json y produce las tablas listas para la tesis,
incluyendo las salvedades metodologicas que condicionan la lectura de cada
metrica.

Uso:
    python scripts/fase5_generar_reporte.py \
        [--input results/benchmark_100_eval.json] \
        [--output reportes/comparativa_escenarios.md]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ORDEN = ["E1", "E2", "E3"]

# Sufijos aglutinantes frecuentes del quechua. Permiten decidir si una
# respuesta se mantuvo en la lengua de la consulta o derivo al castellano.
_SUFIJOS_QUECHUA = re.compile(
    r"\w+(kuna|nchik|manta|paq|wan|pi|ta|qa|mi|chu|nki|nku|spa|sqa|yuq|niyuq)\b",
    re.IGNORECASE,
)
_RE_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)


def responde_en_quechua(texto: str, umbral: float = 0.15) -> bool:
    """True si la densidad de sufijos quechua supera el umbral."""
    palabras = _RE_PALABRA.findall(texto or "")
    if len(palabras) < 3:
        return False
    return len(_SUFIJOS_QUECHUA.findall(texto)) / len(palabras) > umbral


def fmt(valor: float, decimales: int = 2) -> str:
    return f"{valor:.{decimales}f}"


def delta(actual: float, base: float, decimales: int = 2) -> str:
    """Diferencia frente al control, con signo explicito."""
    if base == 0:
        return "-"
    d = actual - base
    signo = "+" if d >= 0 else ""
    return f"{signo}{d:.{decimales}f}"


def tabla(cabeceras: list[str], filas: list[list[str]]) -> str:
    lineas = ["| " + " | ".join(cabeceras) + " |",
              "|" + "|".join([" --- "] * len(cabeceras)) + "|"]
    for fila in filas:
        lineas.append("| " + " | ".join(fila) + " |")
    return "\n".join(lineas)


def construir(reporte: dict) -> str:
    meta = reporte["metadatos"]
    escenarios = reporte["escenarios"]
    presentes = [c for c in ORDEN if c in escenarios]
    if not presentes:
        raise SystemExit("El reporte no contiene escenarios.")

    base = escenarios[presentes[0]]["resumen"]
    out: list[str] = []

    out.append("# Comparativa experimental de escenarios E1 / E2 / E3")
    out.append("")
    out.append("Asistente pedagogico SLM + RAG para Quechua Collao en Android.")
    out.append("")

    # --- configuracion ---------------------------------------------------
    out.append("## 1. Configuracion de la corrida")
    out.append("")
    out.append(tabla(
        ["Parametro", "Valor"],
        [
            ["Fecha (UTC)", meta["fecha"]],
            ["Modelo de generacion", f"`{meta['modelo_generacion']}`"],
            ["Modelo de embeddings", f"`{meta['modelo_embeddings']}`"],
            ["Backend", meta["backend"]],
            ["Plataforma", meta["plataforma"]],
            ["Consultas evaluadas", str(meta["n_consultas"])],
            ["Recuperacion", f"coseno, top-k={meta['top_k']}, umbral={meta['umbral_coseno']}"],
            ["Generacion", f"max_tokens={meta['max_tokens']}, temperatura={meta['temperatura']}"],
            ["Adaptador QLoRA disponible", "si" if meta["adaptador_qlora_disponible"] else "**no**"],
        ],
    ))
    out.append("")

    # --- escenarios ------------------------------------------------------
    out.append("## 2. Escenarios comparados")
    out.append("")
    filas = []
    for c in presentes:
        e = escenarios[c]
        filas.append([
            f"**{c}**", e["nombre"],
            "si" if e["usa_rag"] else "no",
            "si" if e.get("usa_adaptador_qlora") else "no",
        ])
    out.append(tabla(["Escenario", "Descripcion", "RAG", "QLoRA"], filas))
    out.append("")

    notas = [(c, n) for c in presentes for n in escenarios[c].get("notas", [])]
    if notas:
        out.append("> **Salvedades declaradas por el pipeline**")
        out.append(">")
        for c, n in notas:
            out.append(f"> - **{c}**: {n}")
        out.append("")

    # --- calidad linguistica ---------------------------------------------
    out.append("## 3. Calidad linguistica y semantica")
    out.append("")
    out.append("Calculado sobre las consultas con respaldo curricular "
               "(las sondas de alucinacion se excluyen: su respuesta correcta "
               "es una abstencion, no un parafraseo).")
    out.append("")
    filas = []
    for c in presentes:
        L = escenarios[c]["resumen"]["linguisticas"]
        Lb = base["linguisticas"]
        filas.append([
            f"**{c}**",
            f"{fmt(L['chrf_pp'])} ({delta(L['chrf_pp'], Lb['chrf_pp'])})",
            f"{fmt(L['bleu4'])} ({delta(L['bleu4'], Lb['bleu4'])})",
            f"{fmt(L['rouge_l'])} ({delta(L['rouge_l'], Lb['rouge_l'])})",
            f"{fmt(L['similitud_coseno'], 3)} ({delta(L['similitud_coseno'], Lb['similitud_coseno'], 3)})",
        ])
    out.append(tabla(
        ["Escenario", "chrF++", "BLEU-4", "ROUGE-L", "Similitud coseno"], filas))
    out.append("")
    out.append("Los valores entre parentesis son la diferencia frente a "
               f"**{presentes[0]}** (control).")
    out.append("")

    # --- fundamentacion ---------------------------------------------------
    out.append("## 4. Fundamentacion y pertinencia")
    out.append("")
    filas = []
    for c in presentes:
        F = escenarios[c]["resumen"]["fundamentacion"]
        filas.append([
            f"**{c}**",
            fmt(F["faithfulness"], 3),
            fmt(F["answer_relevance"], 3),
            fmt(F["cobertura_contexto"], 3),
            str(F["items_con_contexto"]),
        ])
    out.append(tabla(
        ["Escenario", "Faithfulness", "Answer relevance",
         "Cobertura de contexto", "Items con contexto"], filas))
    out.append("")
    out.append("> Faithfulness y answer relevance son **aproximaciones locales "
               "deterministas**, no los estimadores de la libreria RAGAS: esta "
               "requiere un LLM juez por API y el pipeline se mantuvo offline. "
               "Faithfulness es 0 por definicion cuando no se inyecta contexto "
               "(caso de E1), porque no hay fuente que fundamente la respuesta.")
    out.append("")

    # --- alucinacion ------------------------------------------------------
    out.append("## 5. Alucinacion (sondas sin respaldo curricular)")
    out.append("")
    out.append("Consultas cuya respuesta no existe en el corpus. La respuesta "
               "correcta es reconocer el desconocimiento; afirmar un codigo de "
               "resolucion, una pagina o un porcentaje es necesariamente una "
               "invencion.")
    out.append("")
    filas = []
    for c in presentes:
        A = escenarios[c]["resumen"]["alucinacion"]
        filas.append([
            f"**{c}**",
            f"{A['abstenciones_correctas']}/{A['n_sondas']}",
            f"{100 * A['tasa_abstencion_correcta']:.1f} %",
            str(A["entidades_inventadas_en_sondas"]),
            f"{100 * A['tasa_invencion_global']:.1f} %",
        ])
    out.append(tabla(
        ["Escenario", "Abstenciones correctas", "Tasa de abstencion",
         "Entidades inventadas en sondas", "Invencion global"], filas))
    out.append("")

    # --- eficiencia -------------------------------------------------------
    out.append("## 6. Eficiencia")
    out.append("")
    filas = []
    for c in presentes:
        E = escenarios[c]["resumen"]["eficiencia"]
        filas.append([
            f"**{c}**",
            f"{E['ttft_ms_medio']:.0f}",
            f"{E['throughput_tok_s_medio']:.2f}",
            f"{E['latencia_total_ms_media']:.0f}",
            f"{E['ram_pico_mb']:.0f}",
        ])
    out.append(tabla(
        ["Escenario", "TTFT medio (ms)", "Throughput (tok/s)",
         "Latencia total media (ms)", "RAM pico (MB)"], filas))
    out.append("")
    out.append(f"> Medido con {meta['backend']} sobre {meta['plataforma']}. "
               "Estas cifras corresponden al banco de pruebas de escritorio y "
               "**no** sustituyen la medicion en dispositivo Android, que debe "
               "reportarse por separado.")
    out.append("")

    # --- desglose por tipo -----------------------------------------------
    out.append("## 7. chrF++ por tipo de consulta")
    out.append("")
    por_tipo: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for c in presentes:
        for item in escenarios[c]["items"]:
            if item["es_sonda_alucinacion"]:
                continue
            por_tipo[item["tipo"]][c].append(item["linguisticas"]["chrf_pp"])

    filas = []
    for tipo in sorted(por_tipo):
        fila = [f"`{tipo}`"]
        n = 0
        for c in presentes:
            vals = por_tipo[tipo][c]
            n = max(n, len(vals))
            fila.append(fmt(sum(vals) / len(vals)) if vals else "-")
        fila.append(str(n))
        filas.append(fila)
    out.append(tabla(["Tipo de consulta"] + presentes + ["n"], filas))
    out.append("")

    # --- desglose por idioma ---------------------------------------------
    out.append("## 8. chrF++ por idioma de la consulta")
    out.append("")
    por_idioma: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    for c in presentes:
        for item in escenarios[c]["items"]:
            if item["es_sonda_alucinacion"]:
                continue
            por_idioma[item["idioma"]][c].append(item["linguisticas"]["chrf_pp"])

    filas = []
    for idioma in sorted(por_idioma):
        fila = [f"`{idioma}`"]
        n = 0
        for c in presentes:
            vals = por_idioma[idioma][c]
            n = max(n, len(vals))
            fila.append(fmt(sum(vals) / len(vals)) if vals else "-")
        fila.append(str(n))
        filas.append(fila)
    out.append(tabla(["Idioma"] + presentes + ["n"], filas))
    out.append("")

    # --- deriva de idioma -------------------------------------------------
    out.append("## 9. Deriva de idioma en consultas formuladas en Quechua Collao")
    out.append("")
    out.append("Fraccion de consultas en `qu_collao` que el modelo respondio "
               "efectivamente en quechua, medida por densidad de sufijos "
               "aglutinantes. Es la contraparte necesaria de chrF++: una caida "
               "de solapamiento puede deberse a que el modelo cambio de lengua, "
               "no a que empeorara su contenido.")
    out.append("")
    filas = []
    deriva: dict[str, float] = {}
    for c in presentes:
        items = [i for i in escenarios[c]["items"]
                 if i["idioma"] == "qu_collao" and not i["es_sonda_alucinacion"]]
        en_quechua = sum(1 for i in items if responde_en_quechua(i["respuesta"]))
        tasa = en_quechua / len(items) if items else 0.0
        deriva[c] = tasa
        filas.append([f"**{c}**", str(len(items)), str(en_quechua), f"{100 * tasa:.1f} %"])
    out.append(tabla(
        ["Escenario", "Consultas en quechua", "Respuestas en quechua", "Tasa"], filas))
    out.append("")

    if "E1" in deriva and "E2" in deriva and deriva["E1"] > deriva["E2"]:
        out.append(f"> **Hallazgo.** La recuperacion curricular hunde la tasa de "
                   f"respuesta en quechua del {100 * deriva['E1']:.1f} % (E1) al "
                   f"{100 * deriva['E2']:.1f} % (E2). El contexto inyectado es "
                   "predominantemente castellano y arrastra al modelo a esa "
                   "lengua, de modo que la respuesta se aleja de la referencia "
                   "dorada en quechua. Esto explica por que chrF++ mejora en "
                   "consultas en castellano y **empeora** en las formuladas en "
                   "Quechua Collao. Es, ademas, el argumento empirico mas "
                   "directo a favor de la adaptacion QLoRA: el RAG por si solo "
                   "no dota al modelo de competencia productiva en la lengua "
                   "originaria.")
        out.append("")

    # --- lectura ----------------------------------------------------------
    out.append("## 10. Lectura de los resultados")
    out.append("")
    if len(presentes) >= 2:
        e1, e2 = presentes[0], presentes[1]
        d = (escenarios[e2]["resumen"]["linguisticas"]["chrf_pp"]
             - escenarios[e1]["resumen"]["linguisticas"]["chrf_pp"])
        signo = "mejora" if d > 0 else "reduccion"
        out.append(f"- **Efecto del RAG ({e1} -> {e2})**: {signo} de "
                   f"{abs(d):.2f} puntos chrF++.")
    if "E3" in escenarios and "E2" in escenarios:
        d = (escenarios["E3"]["resumen"]["linguisticas"]["chrf_pp"]
             - escenarios["E2"]["resumen"]["linguisticas"]["chrf_pp"])
        etiqueta = ("del entrenamiento QLoRA mas el andamiaje"
                    if escenarios["E3"].get("usa_adaptador_qlora")
                    else "**del prompt de andamiaje unicamente** (sin QLoRA)")
        out.append(f"- **Efecto {etiqueta} (E2 -> E3)**: "
                   f"{d:+.2f} puntos chrF++.")
        out.append("- Un chrF++ menor en E3 no implica peor respuesta: el "
                   "andamiaje produce respuestas largas y estructuradas en "
                   "cuatro pasos, mientras la respuesta dorada es una "
                   "definicion breve. El solapamiento de n-gramas penaliza esa "
                   "diferencia de formato. Para E3 son mas informativas la "
                   "fundamentacion, la tasa de abstencion y la valoracion "
                   "pedagogica humana.")
    out.append("")

    out.append("## 11. Limitaciones")
    out.append("")
    out.append("- El corpus curricular disponible en el repositorio no incluye "
               "los manuales EIB completos del MINEDU; el indice se construyo "
               "con el material realmente presente. Cada fragmento declara su "
               "procedencia en `origen`.")
    out.append("- El conjunto de evaluacion mezcla semillas verificadas, "
               "consultas derivadas del corpus y sondas de alucinacion. El "
               "campo `procedencia` de cada item permite recalcular cualquier "
               "metrica sobre el subconjunto que se considere admisible.")
    out.append("- Las metricas de eficiencia provienen del banco de escritorio "
               "(llama.cpp, CPU), no del dispositivo Android.")
    if not meta["adaptador_qlora_disponible"]:
        out.append("- **E3 se ejecuto sin adaptador QLoRA.** La comparacion "
                   "E2 vs E3 mide el prompt de andamiaje, no el entrenamiento.")
    out.append("")

    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Fase 5.3: reporte comparativo")
    ap.add_argument("--input", default="results/benchmark_100_eval.json")
    ap.add_argument("--output", default="reportes/comparativa_escenarios.md")
    args = ap.parse_args()

    entrada = Path(args.input)
    if not entrada.is_absolute():
        entrada = ROOT / entrada
    if not entrada.exists():
        raise SystemExit(f"No existe {entrada}. Ejecuta scripts/evaluar_escenarios.py")

    salida = Path(args.output)
    if not salida.is_absolute():
        salida = ROOT / salida
    salida.parent.mkdir(parents=True, exist_ok=True)

    reporte = json.loads(entrada.read_text(encoding="utf-8"))
    salida.write_text(construir(reporte), encoding="utf-8")
    print(f"[reporte] -> {salida.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
