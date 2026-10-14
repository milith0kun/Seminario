"""FASE 1 - Curacion, limpieza y normalizacion de datos Quechua Collao.

Produce, a partir del material realmente disponible en el repositorio:

  data/processed/corpus_collao.jsonl      Corpus monolingue filtrado a Collao
  data/processed/corpus_curricular.jsonl  Fragmentos curriculares EIB segmentados
  data/train/pares_pedagogicos.jsonl      Pares (instruccion, entrada, respuesta) QLoRA

Cada registro conserva su procedencia (`origen`, `fuente`) para que la tesis
pueda distinguir material documental de material derivado.

Uso:
    python scripts/fase1_curar_datos.py [--max-segmentos N]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.datos.normalizador_collao import (  # noqa: E402
    detectar_variante,
    normalizar_trivocalico,
)

DATOS = ROOT / "datos"
DATA = ROOT / "data"
PROCESSED = DATA / "processed"
TRAIN = DATA / "train"

CORPUS_MONOLINGUE = DATOS / "crudos" / "external" / "llamacha_monolingual_quechua.jsonl"
MOTOR_RAG_KT = (
    ROOT.parent
    / "repos-externos/gallery/Android/src/app/src/main/java/com/google/ai/edge/gallery"
    / "rag/QuechuaRagEngine.kt"
)

# Segmentacion curricular pedida por el plan de tesis: 150-300 tokens.
TOKENS_MIN = 150
TOKENS_MAX = 300


def contar_tokens(texto: str) -> int:
    """Estimacion de tokens por palabras (proxy estable y sin dependencias)."""
    return len(re.findall(r"\S+", texto))


# --------------------------------------------------------------------------
# 1.1 Corpus monolingue Collao
# --------------------------------------------------------------------------

def curar_corpus_monolingue(max_segmentos: int | None = None) -> list[dict]:
    """Filtra el corpus monolingue conservando solo segmentos Collao."""
    if not CORPUS_MONOLINGUE.exists():
        print(f"  [omitido] no existe {CORPUS_MONOLINGUE.name}")
        return []

    conservados: list[dict] = []
    conteo = Counter()
    vistos: set[str] = set()

    with CORPUS_MONOLINGUE.open(encoding="utf-8") as f:
        for i, linea in enumerate(f):
            linea = linea.strip()
            if not linea:
                continue
            try:
                registro = json.loads(linea)
            except json.JSONDecodeError:
                conteo["json_invalido"] += 1
                continue

            texto = (registro.get("text") or "").strip()
            texto = re.sub(r"\s+", " ", texto)

            if len(texto) < 40:
                conteo["muy_corto"] += 1
                continue
            # Descarta lineas que son mayoritariamente digitos o simbolos.
            if sum(c.isalpha() for c in texto) < 0.6 * len(texto):
                conteo["no_textual"] += 1
                continue

            clave = texto.lower()[:120]
            if clave in vistos:
                conteo["duplicado"] += 1
                continue

            perfil = detectar_variante(texto)
            conteo[f"variante_{perfil.variante}"] += 1
            if not perfil.es_collao:
                continue

            vistos.add(clave)
            conservados.append(
                {
                    "id": f"collao_{len(conservados):06d}",
                    "texto": texto,
                    "texto_normalizado": normalizar_trivocalico(texto),
                    "variante": perfil.variante,
                    "puntaje_collao": perfil.puntaje_collao,
                    "rasgos": perfil.rasgos,
                    "tokens": contar_tokens(texto),
                    "origen": "corpus_documental",
                    "fuente": "llamacha_monolingual_quechua (filtrado a Collao)",
                    "split_original": registro.get("split", "train"),
                }
            )
            if max_segmentos and len(conservados) >= max_segmentos:
                break

    print(f"  segmentos Collao conservados : {len(conservados)}")
    for k, v in conteo.most_common(8):
        print(f"    {k:26s} {v}")
    return conservados


# --------------------------------------------------------------------------
# 1.2 Corpus curricular EIB
# --------------------------------------------------------------------------

def extraer_chunks_del_motor() -> list[dict]:
    """Extrae los fragmentos curriculares declarados en QuechuaRagEngine.kt.

    Es la unica fuente del repositorio con contenido curricular EIB
    estructurado (area, grado, referencia MINEDU) en Collao y castellano.
    """
    if not MOTOR_RAG_KT.exists():
        print(f"  [omitido] no existe {MOTOR_RAG_KT}")
        return []

    fuente = MOTOR_RAG_KT.read_text(encoding="utf-8")
    bloques = re.findall(r"CurricularChunk\((.*?)\n    \)", fuente, re.DOTALL)

    def campo(bloque: str, nombre: str) -> str:
        m = re.search(rf'{nombre}\s*=\s*"((?:[^"\\]|\\.)*)"', bloque)
        return m.group(1).replace('\\"', '"') if m else ""

    def lista(bloque: str, nombre: str) -> list[str]:
        m = re.search(rf"{nombre}\s*=\s*listOf\((.*?)\)", bloque, re.DOTALL)
        return re.findall(r'"([^"]*)"', m.group(1)) if m else []

    chunks: list[dict] = []
    for bloque in bloques:
        cid = campo(bloque, "id")
        if not cid:
            continue
        contenido_qu = campo(bloque, "contentQuechua")
        contenido_es = campo(bloque, "contentSpanish")
        perfil = detectar_variante(contenido_qu)
        chunks.append(
            {
                "chunk_id": cid,
                "titulo": campo(bloque, "title"),
                "area": campo(bloque, "area"),
                "grado": campo(bloque, "grade"),
                "palabras_clave_qu": lista(bloque, "quechuaKeywords"),
                "palabras_clave_es": lista(bloque, "spanishKeywords"),
                "contenido_qu": contenido_qu,
                "contenido_es": contenido_es,
                "contenido_qu_normalizado": normalizar_trivocalico(contenido_qu),
                "variante_detectada": perfil.variante,
                "referencia": campo(bloque, "sourceRef"),
                "tokens": contar_tokens(f"{contenido_qu} {contenido_es}"),
                "origen": "curricular_estructurado",
                "fuente": "QuechuaRagEngine.kt (base curricular EIB del prototipo)",
            }
        )
    print(f"  fragmentos curriculares extraidos : {len(chunks)}")
    return chunks


def cargar_chunks_muestra() -> list[dict]:
    """Incorpora los fragmentos de muestra ya presentes en datos/corpus_rag."""
    ruta = DATOS / "corpus_rag" / "chunks.jsonl"
    if not ruta.exists():
        return []

    chunks: list[dict] = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.strip():
            continue
        d = json.loads(linea)
        texto = d.get("text", "").strip()
        if not texto:
            continue
        chunks.append(
            {
                "chunk_id": d.get("chunk_id", f"muestra_{len(chunks)}"),
                "titulo": d.get("title", ""),
                "area": d.get("domain", ""),
                "grado": str(d.get("grade", "")),
                "palabras_clave_qu": [],
                "palabras_clave_es": [],
                "contenido_qu": "" if d.get("language") == "es" else texto,
                "contenido_es": texto if d.get("language") == "es" else "",
                "contenido_qu_normalizado": "",
                "variante_detectada": detectar_variante(texto).variante,
                "referencia": d.get("source_ref", ""),
                "tokens": contar_tokens(texto),
                "origen": "muestra_prototipo",
                "fuente": "datos/corpus_rag/chunks.jsonl (material de muestra)",
            }
        )
    print(f"  fragmentos de muestra incorporados : {len(chunks)}")
    return chunks


# Lexico que marca un segmento como pedagogicamente aprovechable. Permite
# rescatar material curricular real del corpus Collao cuando no se dispone de
# los manuales EIB del MINEDU en el repositorio.
_LEXICO_EDUCATIVO = {
    "yachay": "Educacion y saberes",
    "yachachiq": "Educacion y saberes",
    "yachaywasi": "Educacion y saberes",
    "wawa": "Personal Social",
    "warma": "Personal Social",
    "ayllu": "Personal Social",
    "llaqta": "Personal Social",
    "allpa": "Ciencia y Tecnologia",
    "yaku": "Ciencia y Tecnologia",
    "yura": "Ciencia y Tecnologia",
    "sacha": "Ciencia y Tecnologia",
    "uywa": "Ciencia y Tecnologia",
    "chakra": "Ciencia y Tecnologia",
    "inti": "Ciencia y Tecnologia",
    "killa": "Ciencia y Tecnologia",
    "yupay": "Matematica",
    "chunka": "Matematica",
    "pachak": "Matematica",
    "simi": "Comunicacion",
    "rimay": "Comunicacion",
    "willakuy": "Comunicacion",
    "harawi": "Comunicacion",
}


def enriquecer_desde_corpus_collao(
    monolingue: list[dict], objetivo: int = 40
) -> list[dict]:
    """Selecciona segmentos Collao con carga tematica escolar.

    No son manuales MINEDU: son textos documentales reales en Quechua Collao
    que aportan cobertura tematica al indice RAG. Quedan marcados con
    `origen='corpus_documental_collao'` para no confundirlos con fuente oficial.
    """
    candidatos: list[tuple[int, dict, str]] = []
    for seg in monolingue:
        texto = seg["texto"]
        if not (12 <= seg["tokens"] <= TOKENS_MAX):
            continue
        bajo = texto.lower()
        areas = [area for termino, area in _LEXICO_EDUCATIVO.items() if termino in bajo]
        if not areas:
            continue
        # Prioriza segmentos con mas rasgos Collao y mas carga tematica.
        puntaje = seg["puntaje_collao"] + 2 * len(areas)
        area = Counter(areas).most_common(1)[0][0]
        candidatos.append((puntaje, seg, area))

    candidatos.sort(key=lambda x: x[0], reverse=True)

    chunks: list[dict] = []
    for puntaje, seg, area in candidatos[:objetivo]:
        chunks.append(
            {
                "chunk_id": f"collao_doc_{len(chunks):03d}",
                "titulo": f"Texto documental Collao - {area}",
                "area": area,
                "grado": "primaria EIB",
                "palabras_clave_qu": [
                    t for t in _LEXICO_EDUCATIVO if t in seg["texto"].lower()
                ][:6],
                "palabras_clave_es": [],
                "contenido_qu": seg["texto"],
                "contenido_es": "",
                "contenido_qu_normalizado": seg["texto_normalizado"],
                "variante_detectada": seg["variante"],
                "referencia": seg["fuente"],
                "tokens": seg["tokens"],
                "origen": "corpus_documental_collao",
                "fuente": seg["fuente"],
                "puntaje_collao": puntaje,
            }
        )
    print(f"  fragmentos rescatados del corpus Collao : {len(chunks)}")
    return chunks


def segmentar(chunks: list[dict]) -> list[dict]:
    """Divide fragmentos que exceden TOKENS_MAX, respetando limites de oracion."""
    salida: list[dict] = []
    for chunk in chunks:
        cuerpo = f"{chunk['contenido_es']}".strip()
        if chunk["tokens"] <= TOKENS_MAX or not cuerpo:
            salida.append(chunk)
            continue

        oraciones = re.split(r"(?<=[.!?])\s+", cuerpo)
        actual: list[str] = []
        parte = 0
        for oracion in oraciones:
            actual.append(oracion)
            if contar_tokens(" ".join(actual)) >= TOKENS_MIN:
                nuevo = dict(chunk)
                nuevo["chunk_id"] = f"{chunk['chunk_id']}_p{parte}"
                nuevo["contenido_es"] = " ".join(actual)
                nuevo["tokens"] = contar_tokens(" ".join(actual))
                salida.append(nuevo)
                actual, parte = [], parte + 1
        if actual:
            nuevo = dict(chunk)
            nuevo["chunk_id"] = f"{chunk['chunk_id']}_p{parte}"
            nuevo["contenido_es"] = " ".join(actual)
            nuevo["tokens"] = contar_tokens(" ".join(actual))
            salida.append(nuevo)
    return salida


# --------------------------------------------------------------------------
# 1.3 Pares pedagogicos para QLoRA
# --------------------------------------------------------------------------

PLANTILLAS_INSTRUCCION = [
    ("Explica a un estudiante de {grado} que es {tema}, en castellano y Quechua Collao.",
     "bilingue_explicativo"),
    ("Como docente EIB, guia con andamiaje a un estudiante que pregunta sobre {tema}.",
     "andamiaje_pedagogico"),
    ("Responde en Quechua Collao la siguiente consulta escolar sobre {tema}.",
     "respuesta_quechua"),
    ("Formula una pregunta orientadora para activar saberes previos sobre {tema}.",
     "pregunta_orientadora"),
]


def construir_pares_pedagogicos(curriculares: list[dict]) -> list[dict]:
    """Genera pares instruccion/entrada/respuesta anclados al corpus curricular.

    Las respuestas se construyen a partir del contenido curricular recuperado,
    no se inventan: cada par cita su fragmento de origen en `fuente_chunk`.
    """
    pares: list[dict] = []
    for chunk in curriculares:
        if not chunk["contenido_es"]:
            continue
        tema = chunk["titulo"] or chunk["area"]
        grado = chunk["grado"] or "primaria"

        for plantilla, tipo in PLANTILLAS_INSTRUCCION:
            instruccion = plantilla.format(tema=tema, grado=grado)

            if tipo == "bilingue_explicativo":
                respuesta = (
                    f"{chunk['contenido_es']}\n\n"
                    f"Quechua Collao: {chunk['contenido_qu']}"
                ).strip()
            elif tipo == "andamiaje_pedagogico":
                clave = (chunk["palabras_clave_qu"] or ["yachay"])[0]
                respuesta = (
                    f"Allillanchu wawqiy. Antes de explicarte, observa tu entorno: "
                    f"que sabes ya sobre {tema.lower()}?\n"
                    f"Pista en Quechua Collao: '{clave}'.\n"
                    f"Ahora la explicacion: {chunk['contenido_es']}\n"
                    f"Ejemplo del entorno andino: relacionalo con lo que ves en tu "
                    f"chacra o comunidad."
                )
            elif tipo == "respuesta_quechua":
                if not chunk["contenido_qu"]:
                    continue
                respuesta = chunk["contenido_qu"]
            else:
                respuesta = (
                    f"Imatan yachanki {tema.lower()} nisqamanta? "
                    f"Que has observado en tu comunidad sobre esto?"
                )

            pares.append(
                {
                    "id": f"par_{len(pares):05d}",
                    "instruccion": instruccion,
                    "entrada": "",
                    "respuesta": respuesta,
                    "tipo": tipo,
                    "area": chunk["area"],
                    "grado": grado,
                    "fuente_chunk": chunk["chunk_id"],
                    "referencia": chunk["referencia"],
                    "origen": "derivado_de_corpus_curricular",
                }
            )
    print(f"  pares pedagogicos generados : {len(pares)}")
    return pares


# --------------------------------------------------------------------------

def escribir_jsonl(ruta: Path, registros: list[dict]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("w", encoding="utf-8") as f:
        for r in registros:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"  -> {ruta.relative_to(ROOT)}  ({len(registros)} registros)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Fase 1: curacion de datos Quechua Collao")
    ap.add_argument("--max-segmentos", type=int, default=20000,
                    help="Tope de segmentos Collao a conservar del corpus monolingue")
    args = ap.parse_args()

    print("[1/3] Corpus monolingue -> filtrado dialectal Collao")
    monolingue = curar_corpus_monolingue(args.max_segmentos)
    escribir_jsonl(PROCESSED / "corpus_collao.jsonl", monolingue)

    print("\n[2/3] Corpus curricular EIB -> segmentacion 150-300 tokens")
    curriculares = segmentar(
        extraer_chunks_del_motor()
        + cargar_chunks_muestra()
        + enriquecer_desde_corpus_collao(monolingue, objetivo=40)
    )
    escribir_jsonl(PROCESSED / "corpus_curricular.jsonl", curriculares)

    print("\n[3/3] Pares pedagogicos para QLoRA")
    pares = construir_pares_pedagogicos(curriculares)
    escribir_jsonl(TRAIN / "pares_pedagogicos.jsonl", pares)

    print("\nResumen:")
    print(f"  corpus Collao      : {len(monolingue)} segmentos")
    print(f"  corpus curricular  : {len(curriculares)} fragmentos")
    print(f"  pares QLoRA        : {len(pares)}")


if __name__ == "__main__":
    main()
