"""Pruebas de los modulos del pipeline experimental (fases 1, 2 y 4)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.datos.normalizador_collao import (  # noqa: E402
    detectar_variante,
    normalizar_trivocalico,
    validar_alfabeto,
)
from src.evaluacion import metricas as M  # noqa: E402


# --- Fase 1: deteccion dialectal -------------------------------------------

@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("Qusqu Qullaw qhichwa simi", "collao"),
        ("Yurakunaqa inti k'anchaywan mikhunankuta ruwanku", "collao"),
        ("Nuqaqa yachachkani wasiypi", "chanka"),
        ("Warmakunaqa hamuchkanku llaqtamanta", "chanka"),
    ],
)
def test_detecta_variante_dialectal(texto, esperado):
    assert detectar_variante(texto).variante == esperado


def test_texto_sin_rasgos_no_se_asigna_por_defecto():
    """Sin evidencia fonologica la variante queda indeterminada, no 'collao'."""
    assert detectar_variante("wasi runa allin").variante == "indeterminado"


# --- Fase 1: normalizacion trivocalica -------------------------------------

def test_normaliza_vocales_medias_a_trivocalico():
    assert normalizar_trivocalico("Qosqo llaqta") == "Qusqu llaqta"


def test_no_destruye_secuencia_qu_legitima():
    """Regresion: un reemplazo ciego de 'qu' convertia 'Qosqo' en 'Ksk'."""
    resultado = normalizar_trivocalico("Qosqo")
    assert resultado == "Qusqu"
    assert "k" not in resultado.lower()


def test_preserva_prestamos_del_castellano():
    original = "Los estudiantes de ciencia y tecnologia"
    assert normalizar_trivocalico(original) == original


def test_preserva_plurales_de_prestamos():
    assert "plantas" in normalizar_trivocalico("Las plantas verdes")


def test_convierte_grafia_hispanizante():
    assert normalizar_trivocalico("huahua") == "wawa"


def test_validar_alfabeto_detecta_grafias_no_oficiales():
    assert "o" in validar_alfabeto("Qosqo")
    assert validar_alfabeto("qusqu llaqta") == []


# --- Fase 4: metricas linguisticas -----------------------------------------

def test_chrf_premia_coincidencia_exacta():
    texto = "Yurakunaqa inti k'anchaywan mikhunku"
    assert M.chrf_pp(texto, texto) == pytest.approx(100.0, abs=0.5)


def test_chrf_es_cero_con_texto_vacio():
    assert M.chrf_pp("", "referencia") == 0.0


def test_rouge_l_ordena_por_solapamiento():
    ref = "las plantas producen alimento con luz solar"
    alta = "las plantas producen alimento con luz"
    baja = "el gato duerme sobre la mesa"
    assert M.rouge_l(alta, ref) > M.rouge_l(baja, ref)


def test_bleu4_no_penaliza_frases_cortas_por_falta_de_4gramas():
    """effective_order evita el 0 artificial en respuestas breves."""
    assert M.bleu4("Oxigeno.", "Oxigeno.") > 0


# --- Fase 4: fundamentacion -------------------------------------------------

def test_faithfulness_es_cero_sin_contexto():
    """Sin fuentes no hay nada que fundamentar: la metrica no debe valer 1."""
    assert M.faithfulness("Las plantas usan luz solar para su alimento.", []) == 0.0


def test_faithfulness_distingue_respaldo_de_invencion():
    contexto = [
        "Las plantas producen su alimento mediante la luz solar, el agua de "
        "las raices y el dioxido de carbono del aire."
    ]
    respaldada = "Las plantas producen su alimento con luz solar, agua y dioxido de carbono."
    inventada = "El ministro firmo la resolucion durante la ceremonia del martes pasado."
    assert M.faithfulness(respaldada, contexto) > M.faithfulness(inventada, contexto)


def test_similitud_coseno_de_vectores_ortogonales_es_cero():
    assert M.similitud_coseno(np.array([1.0, 0.0]), np.array([0.0, 1.0])) == 0.0


def test_similitud_coseno_tolera_vector_nulo():
    assert M.similitud_coseno(np.zeros(3), np.ones(3)) == 0.0


# --- Fase 4: alucinacion ----------------------------------------------------

@pytest.mark.parametrize(
    "texto",
    [
        "No dispongo de esa informacion en el material curricular.",
        "No se especifica en el documento proporcionado.",
        "Corresponde consultar la fuente oficial del MINEDU.",
    ],
)
def test_reconoce_abstenciones(texto):
    assert M.es_abstencion(texto)


def test_no_confunde_respuesta_afirmativa_con_abstencion():
    assert not M.es_abstencion("La fotosintesis ocurre en las hojas.")


def test_detecta_entidades_inventadas():
    assert M.inventa_entidad("Segun la RM 1218-85-ED, pagina 42, aprobo el 68%.")


def test_abstenerse_no_cuenta_como_invencion():
    """Una abstencion que menciona una norma no debe marcarse como alucinacion."""
    assert not M.inventa_entidad(
        "No dispongo de ese dato; consulte la RM 1218-85-ED en el portal oficial."
    )


# --- Fase 2: indice vectorial ----------------------------------------------

@pytest.fixture(scope="module")
def indice():
    directorio = ROOT / "data" / "processed" / "indice_vectorial"
    if not (directorio / "embeddings.npy").exists():
        pytest.skip("Indice no construido; ejecuta scripts/fase2_construir_indice.py")

    from src.rag.indice_vectorial import IndiceVectorial

    for candidato in [
        ROOT / "modelos" / "embeddings" / "multilingual-e5-small",
        ROOT.parent / "modelos" / "embeddings" / "multilingual-e5-small",
    ]:
        if (candidato / "config.json").exists():
            return IndiceVectorial.cargar(directorio, candidato)
    pytest.skip("Modelo de embeddings no disponible")


def test_indice_recupera_fragmento_pertinente(indice):
    resultado = indice.recuperar("Que es la fotosintesis?", top_k=3)
    assert resultado.hubo_recuperacion
    assert resultado.similitud_maxima > 0.8


def test_guardarrail_descarta_consulta_sin_respaldo(indice):
    """La sonda pide una entidad ausente del corpus: no debe inyectar contexto."""
    resultado = indice.recuperar(
        "Cual es el codigo de la Resolucion Ministerial que aprobo el area de "
        "Robotica Educativa EIB en Quechua Collao?",
        top_k=3,
    )
    assert resultado.sin_respaldo
    assert not resultado.hubo_recuperacion


def test_embeddings_estan_normalizados(indice):
    """El coseno se calcula como producto punto: las filas deben tener norma 1."""
    normas = np.linalg.norm(indice.matriz, axis=1)
    assert np.allclose(normas, 1.0, atol=1e-4)
