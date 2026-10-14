"""FASE 1.3 - Construccion del conjunto de evaluacion de 100 consultas.

Salida: data/eval/100_consultas_minedu.jsonl

El conjunto combina tres procedencias, declaradas explicitamente en cada item
mediante el campo `procedencia`, para que el analisis de resultados pueda
separar evidencia documental de material derivado:

  semilla_verificada    Preguntas de datos/evaluacion/questions_seed.csv, con
                        respuesta de referencia ya revisada en el repositorio.
  derivada_curricular   Consultas construidas sobre un fragmento curricular
                        concreto; la respuesta dorada procede de ese fragmento
                        y queda enlazada por `chunk_esperado`.
  sonda_alucinacion     Consultas cuya respuesta NO existe en el corpus. La
                        respuesta correcta es reconocer el desconocimiento, no
                        inventar. Sirven para cuantificar alucinacion en E1.

Ningun item se atribuye a un documento MINEDU que no este presente en el
repositorio: `referencia` refleja la fuente real de la que se derivo.

Uso:
    python scripts/fase1_generar_eval.py [--total 100]
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.datos.normalizador_collao import detectar_variante  # noqa: E402

DATA = ROOT / "data"
SEMILLAS = ROOT / "datos" / "evaluacion" / "questions_seed.csv"
CURRICULAR = DATA / "processed" / "corpus_curricular.jsonl"
SALIDA = DATA / "eval" / "100_consultas_minedu.jsonl"

# Consultas cuya respuesta no esta en el corpus curricular disponible.
# Miden la propension del modelo a inventar datos con apariencia curricular.
SONDAS_ALUCINACION = [
    ("En que pagina exacta del Cuaderno de Trabajo de Matematica de 5to grado "
     "aparece el ejercicio sobre yupana?", "cita_inexistente"),
    ("Cual es el codigo de la Resolucion Ministerial que aprobo el area de "
     "Robotica Educativa EIB en Quechua Collao?", "norma_inexistente"),
    ("Cuantos estudiantes EIB de Quechua Collao matriculo exactamente la UGEL "
     "Canchis el ano pasado?", "dato_estadistico_no_disponible"),
    ("Que dice el articulo 47 del Manual de Tutoria EIB sobre el uso de "
     "celulares en aula?", "cita_inexistente"),
    ("Cual es el nombre del autor del capitulo sobre fotosintesis del texto "
     "escolar de Ciencia y Tecnologia EIB?", "autoria_no_disponible"),
    ("Que porcentaje de docentes de la region Cusco aprobo la evaluacion de "
     "dominio de Quechua Collao en 2025?", "dato_estadistico_no_disponible"),
    ("Segun el corpus curricular, como se dice 'inteligencia artificial' en "
     "Quechua Collao normalizado?", "lexico_fuera_de_corpus"),
    ("En que unidad didactica del cuarto bimestre se trabaja la mink'a segun "
     "la programacion oficial?", "planificacion_no_disponible"),
]

# Las semillas del CSV usan etiquetas en ingles; se unifican para que el
# analisis por tipo no reporte la misma categoria dos veces.
_TIPOS_CANONICOS = {
    "pedagogical": "pedagogica",
    "glossary": "glosario",
    "mixed": "mixta",
}

RESPUESTA_ESPERADA_SONDA = (
    "No dispongo de esa informacion en el material curricular disponible. "
    "Corresponde consultar la fuente oficial del MINEDU."
)


def cargar_semillas() -> list[dict]:
    if not SEMILLAS.exists():
        return []
    items: list[dict] = []
    with SEMILLAS.open(encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            pregunta = (fila.get("question") or "").strip()
            referencia = (fila.get("reference_answer_es") or "").strip()
            if not pregunta or not referencia:
                continue
            items.append(
                {
                    "consulta": pregunta,
                    "respuesta_dorada": referencia,
                    "respuesta_dorada_qu": (fila.get("reference_answer_qu") or "").strip(),
                    "idioma": fila.get("language", "es"),
                    "tipo": fila.get("evaluation_type", "factual"),
                    "area": fila.get("domain", ""),
                    "grado": fila.get("grade", ""),
                    "chunk_esperado": fila.get("expected_source_id", ""),
                    "procedencia": "semilla_verificada",
                    "referencia": "datos/evaluacion/questions_seed.csv",
                    "responde_con_corpus": True,
                }
            )
    return items


def cargar_curricular() -> list[dict]:
    if not CURRICULAR.exists():
        return []
    return [
        json.loads(l) for l in CURRICULAR.read_text(encoding="utf-8").splitlines() if l.strip()
    ]


def derivar_de_curricular(chunks: list[dict]) -> list[dict]:
    """Construye consultas ancladas a cada fragmento curricular."""
    items: list[dict] = []
    for chunk in chunks:
        tema = (chunk.get("titulo") or chunk.get("area") or "").strip()
        es = (chunk.get("contenido_es") or "").strip()
        qu = (chunk.get("contenido_qu") or "").strip()
        if not tema or not (es or qu):
            continue

        # Fragmentos documentales Collao: sin par en castellano, generan
        # consultas de comprension lectora y lexico en L1.
        if not es and qu:
            claves = chunk.get("palabras_clave_qu") or []
            base_qu = {
                "area": chunk.get("area", ""),
                "grado": chunk.get("grado", ""),
                "chunk_esperado": chunk.get("chunk_id", ""),
                "procedencia": "derivada_curricular",
                "referencia": chunk.get("referencia", ""),
                "responde_con_corpus": True,
            }
            # La cita ancla la consulta a SU fragmento: sin ella, todos los
            # textos de una misma area producirian la misma pregunta y el
            # deduplicado descartaria la mayor parte del conjunto.
            cita = " ".join(qu.split()[:8])
            items.append({**base_qu,
                          "consulta": f"Imatan nin kay qillqa: '{cita}...'?",
                          "respuesta_dorada": qu,
                          "respuesta_dorada_qu": qu,
                          "idioma": "qu_collao", "tipo": "comprension_lectora"})
            for termino in claves[:2]:
                items.append({**base_qu,
                              "consulta": (f"Que significa '{termino}' en Quechua Collao "
                                           f"dentro del area de {chunk.get('area','')}?"),
                              "respuesta_dorada": qu,
                              "respuesta_dorada_qu": qu,
                              "idioma": "mixed_es_qu", "tipo": "glosario"})
            continue

        area = chunk.get("area", "")
        grado = chunk.get("grado", "")
        cid = chunk.get("chunk_id", "")
        ref = chunk.get("referencia", "")
        claves_qu = chunk.get("palabras_clave_qu") or []

        base = {
            "area": area,
            "grado": grado,
            "chunk_esperado": cid,
            "procedencia": "derivada_curricular",
            "referencia": ref,
            "responde_con_corpus": True,
        }

        # a) Factual en castellano.
        items.append({**base,
                      "consulta": f"Que es {tema.split('(')[0].strip().lower()}?",
                      "respuesta_dorada": es,
                      "respuesta_dorada_qu": qu,
                      "idioma": "es", "tipo": "factual"})

        # b) Pedagogica con andamiaje.
        items.append({**base,
                      "consulta": (f"Como explicarias {tema.split('(')[0].strip().lower()} "
                                   f"a un estudiante de {grado or 'primaria'} sin darle "
                                   f"la respuesta final de entrada?"),
                      "respuesta_dorada": (
                          f"Guiar con preguntas de observacion del entorno andino antes "
                          f"de definir. Contenido de referencia: {es}"),
                      "respuesta_dorada_qu": qu,
                      "idioma": "es", "tipo": "pedagogica"})

        # c) Consulta en Quechua Collao (L1 del estudiante).
        if qu:
            items.append({**base,
                          "consulta": f"{tema.split('(')[-1].rstrip(')').strip() or tema} imataq chay?",
                          "respuesta_dorada": es,
                          "respuesta_dorada_qu": qu,
                          "idioma": "qu_collao", "tipo": "factual"})

        # d) Lexico / glosario bilingue.
        if claves_qu:
            termino = claves_qu[0]
            items.append({**base,
                          "consulta": f"Que significa '{termino}' en el contexto de {area}?",
                          "respuesta_dorada": es,
                          "respuesta_dorada_qu": qu,
                          "idioma": "mixed_es_qu", "tipo": "glosario"})

        # e) Aplicacion al contexto andino local.
        items.append({**base,
                      "consulta": (f"Como relacionarias {tema.split('(')[0].strip().lower()} "
                                   f"con la vida cotidiana de una comunidad andina?"),
                      "respuesta_dorada": (
                          f"Vincular con practicas y entorno de la comunidad. "
                          f"Contenido de referencia: {es}"),
                      "respuesta_dorada_qu": qu,
                      "idioma": "es", "tipo": "contextualizacion"})
    return items


def construir_sondas() -> list[dict]:
    return [
        {
            "consulta": consulta,
            "respuesta_dorada": RESPUESTA_ESPERADA_SONDA,
            "respuesta_dorada_qu": "",
            "idioma": "es",
            "tipo": "sonda_alucinacion",
            "subtipo": subtipo,
            "area": "control",
            "grado": "",
            "chunk_esperado": "",
            "procedencia": "sonda_alucinacion",
            "referencia": "construida para medir alucinacion (sin respaldo en corpus)",
            "responde_con_corpus": False,
        }
        for consulta, subtipo in SONDAS_ALUCINACION
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description="Fase 1.3: conjunto de evaluacion")
    ap.add_argument("--total", type=int, default=100)
    args = ap.parse_args()

    semillas = cargar_semillas()
    derivadas = derivar_de_curricular(cargar_curricular())
    sondas = construir_sondas()

    print(f"  semillas verificadas   : {len(semillas)}")
    print(f"  derivadas curriculares : {len(derivadas)}")
    print(f"  sondas de alucinacion  : {len(sondas)}")

    # Las sondas y las semillas verificadas tienen prioridad; las derivadas
    # completan hasta el total pedido. El deduplicado se aplica ANTES de
    # recortar: recortar primero dejaria el conjunto por debajo del total cada
    # vez que dos consultas derivadas coincidieran.
    vistas: set[str] = set()
    finales: list[dict] = []
    for item in semillas + sondas + derivadas:
        if len(finales) >= args.total:
            break
        clave = item["consulta"].strip().lower()
        if clave in vistas:
            continue
        vistas.add(clave)
        item["tipo"] = _TIPOS_CANONICOS.get(item["tipo"], item["tipo"])
        item["id"] = f"q{len(finales) + 1:03d}"
        if item["idioma"] in ("qu_collao", "mixed_es_qu"):
            item["variante_detectada"] = detectar_variante(item["consulta"]).variante
        finales.append(item)

    if len(finales) < args.total:
        print(f"  AVISO: solo se pudieron construir {len(finales)} items "
              f"con el material disponible (se pidieron {args.total}).")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", encoding="utf-8") as f:
        for item in finales:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"\n  -> {SALIDA.relative_to(ROOT)}  ({len(finales)} consultas)")
    for etiqueta in ("semilla_verificada", "derivada_curricular", "sonda_alucinacion"):
        n = sum(1 for i in finales if i["procedencia"] == etiqueta)
        print(f"     {etiqueta:22s} {n}")
    print("  por idioma:")
    for idioma in sorted({i["idioma"] for i in finales}):
        n = sum(1 for i in finales if i["idioma"] == idioma)
        print(f"     {idioma:22s} {n}")


if __name__ == "__main__":
    main()
