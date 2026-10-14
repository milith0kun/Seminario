"""Normalizacion ortografica y deteccion dialectal para Quechua Collao (quz/quh).

Base normativa: RM 1218-85-ED (Alfabeto Oficial de la Lengua Quechua, 31 grafias,
sistema trivocalico a / i / u).

El modulo cubre dos necesidades de la Fase 1 del pipeline de tesis:

1. `detectar_variante`: separar Quechua Collao (Cusco-Qullaw) de Chanka (Ayacucho)
   y de otras variantes, usando los rasgos fonologicos que las distinguen.
2. `normalizar_trivocalico`: llevar el texto a la ortografia oficial trivocalica
   sin destruir prestamos del castellano ni nombres propios.

Rasgos discriminantes usados (fonologia comparada quechua):
  - Collao POSEE consonantes aspiradas (ph, th, chh, kh, qh) y glotalizadas
    (p', t', ch', k', q'). Chanka NO las tiene.
  - Chanka usa el sufijo evidencial -mi/-m y la forma "-chka-" (progresivo);
    Collao usa "-sha-" / "-sya-".
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# --- Alfabeto oficial RM 1218-85-ED -----------------------------------------

VOCALES_OFICIALES = frozenset("aiu")

# 31 grafias del alfabeto oficial (digrafos incluidos).
GRAFIAS_OFICIALES: tuple[str, ...] = (
    "a", "ch", "chh", "ch'", "h", "i", "k", "kh", "k'", "l", "ll", "m", "n",
    "ñ", "p", "ph", "p'", "q", "qh", "q'", "r", "s", "sh", "t", "th", "t'",
    "u", "w", "y", "n", "ll",
)

# --- Rasgos dialectales ------------------------------------------------------

_ASPIRADAS = re.compile(r"(chh|ph|th|kh|qh)", re.IGNORECASE)
_GLOTALIZADAS = re.compile(r"(ch'|p'|t'|k'|q')", re.IGNORECASE)

# Progresivo: Chanka -chka- / -chka; Collao -sha- / -sya-.
_PROGRESIVO_CHANKA = re.compile(r"\w+chka\w*", re.IGNORECASE)
_PROGRESIVO_COLLAO = re.compile(r"\w+(sha|sya)\w*", re.IGNORECASE)

# Lexico tipico de Ancash (excluido por la tesis).
_MARCADORES_ANCASH = re.compile(
    r"\b(nuqantsik|qamkuna|kanan|aywa|tsay|tsaynaw|kuyay)\b", re.IGNORECASE
)

# --- Prestamos y excepciones a la normalizacion trivocalica ------------------

# Terminos castellanos frecuentes en material curricular EIB que NO deben
# trivocalizarse (perderian legibilidad y no son raiz quechua).
_PRESTAMOS_CASTELLANO = frozenset(
    """
    escuela colegio profesor profesora maestro maestra estudiante alumno alumna
    ciencia tecnologia matematica comunicacion personal social arte cultura
    educacion curriculo competencia capacidad desempeno area grado primaria
    secundaria inicial ministerio peru region cusco puno provincia distrito
    comunidad proyecto texto cuaderno libro pagina numero ejemplo ejercicio
    problema respuesta pregunta actividad sesion unidad experiencia evaluacion
    fotosintesis clorofila oxigeno carbono energia planta plantas agua sol
    proceso sistema metodo material recurso docente aula bilingue intercultural
    quechua castellano espanol lengua idioma dialecto alfabeto ortografia
    gobierno estado nacion ciudadano derecho deber salud higiene alimento
    nutricion vitamina mineral animal medio ambiente ecosistema naturaleza
    """.split()
)

# Nombres propios y siglas que se preservan tal cual.
_RE_SIGLA = re.compile(r"^[A-ZÁÉÍÓÚÑ]{2,}$")
_RE_NUMERO = re.compile(r"^[\d.,:/-]+$")

_RE_TOKEN = re.compile(r"[^\W\d_]+(?:'[^\W\d_]+)*|\d+|\s+|[^\w\s]", re.UNICODE)


@dataclass
class PerfilDialectal:
    """Resultado de la deteccion dialectal de un texto."""

    variante: str  # "collao" | "chanka" | "ancash" | "indeterminado"
    puntaje_collao: int = 0
    puntaje_chanka: int = 0
    puntaje_ancash: int = 0
    rasgos: list[str] = field(default_factory=list)

    @property
    def es_collao(self) -> bool:
        return self.variante == "collao"


def detectar_variante(texto: str) -> PerfilDialectal:
    """Clasifica un texto quechua por variante dialectal.

    La deteccion es conservadora: solo declara "collao" ante evidencia
    fonologica positiva (aspiradas o glotalizadas), porque son rasgos que
    Chanka no puede producir. Un texto sin rasgos discriminantes queda como
    "indeterminado" en lugar de asignarse por defecto.
    """
    rasgos: list[str] = []

    aspiradas = _ASPIRADAS.findall(texto)
    glotalizadas = _GLOTALIZADAS.findall(texto)
    prog_chanka = _PROGRESIVO_CHANKA.findall(texto)
    prog_collao = _PROGRESIVO_COLLAO.findall(texto)
    ancash = _MARCADORES_ANCASH.findall(texto)

    puntaje_collao = 3 * len(aspiradas) + 3 * len(glotalizadas) + len(prog_collao)
    puntaje_chanka = 2 * len(prog_chanka)
    puntaje_ancash = 3 * len(ancash)

    if aspiradas:
        rasgos.append(f"aspiradas={len(aspiradas)}")
    if glotalizadas:
        rasgos.append(f"glotalizadas={len(glotalizadas)}")
    if prog_chanka:
        rasgos.append(f"progresivo_chka={len(prog_chanka)}")
    if prog_collao:
        rasgos.append(f"progresivo_sha={len(prog_collao)}")
    if ancash:
        rasgos.append(f"lexico_ancash={len(ancash)}")

    if puntaje_ancash > puntaje_collao and puntaje_ancash > puntaje_chanka:
        variante = "ancash"
    elif puntaje_collao > 0 and puntaje_collao >= puntaje_chanka:
        variante = "collao"
    elif puntaje_chanka > 0:
        variante = "chanka"
    else:
        variante = "indeterminado"

    return PerfilDialectal(
        variante=variante,
        puntaje_collao=puntaje_collao,
        puntaje_chanka=puntaje_chanka,
        puntaje_ancash=puntaje_ancash,
        rasgos=rasgos,
    )


# Palabras funcionales del castellano: si se trivocalizaran, el texto bilingue
# quedaria ilegible ("los" -> "lus", "de" -> "di").
_FUNCIONALES_CASTELLANO = frozenset(
    """
    el la los las un una unos unas de del al a ante bajo con contra desde en
    entre hacia hasta para por segun sin sobre tras y e o u ni que quien cual
    cuyo como cuando donde porque pues si no se le les lo me te nos os su sus
    mi mis tu tus nuestro nuestra vuestro es son era eran fue fueron ser estar
    esta estan este esta estos estas ese esa esos esas aquel aquella hay haber
    tiene tienen tener hacer puede pueden debe deben muy mas menos tambien
    """.split()
)

# Sufijos derivativos exclusivos del castellano.
_SUFIJOS_CASTELLANO = (
    "cion", "ciones", "dad", "dades", "mente", "ando", "iendo", "aje",
    "ismo", "ista", "encia", "ancia", "idad", "logia", "grafia",
)


def _es_prestamo(token: str) -> bool:
    """True si el token debe preservarse sin trivocalizar."""
    if _RE_NUMERO.match(token) or _RE_SIGLA.match(token):
        return True

    plano = "".join(
        c for c in unicodedata.normalize("NFD", token.lower())
        if unicodedata.category(c) != "Mn"
    )
    if plano in _PRESTAMOS_CASTELLANO or plano in _FUNCIONALES_CASTELLANO:
        return True

    # Plurales castellanos de terminos ya listados ("estudiantes", "plantas").
    for sufijo in ("es", "s"):
        if plano.endswith(sufijo):
            singular = plano[: -len(sufijo)]
            if singular in _PRESTAMOS_CASTELLANO or singular in _FUNCIONALES_CASTELLANO:
                return True

    return plano.endswith(_SUFIJOS_CASTELLANO)


def _aplicar_caso(original: str, normalizado: str) -> str:
    """Reaplica la capitalizacion del token original al normalizado."""
    if original.isupper() and len(original) > 1:
        return normalizado.upper()
    if original[:1].isupper():
        return normalizado[:1].upper() + normalizado[1:]
    return normalizado


def normalizar_trivocalico(texto: str, *, preservar_prestamos: bool = True) -> str:
    """Convierte texto quechua al sistema trivocalico oficial (a, i, u).

    Las vocales medias e/o son alofonos de i/u en contacto con /q/ y no forman
    parte del alfabeto oficial, por lo que se normalizan. Los prestamos del
    castellano se preservan si `preservar_prestamos` es True, para no degradar
    tecnicismos curriculares ("ciencia" no debe volverse "cinicia").
    """
    salida: list[str] = []
    for token in _RE_TOKEN.findall(texto):
        if not token.strip() or not any(c.isalpha() for c in token):
            salida.append(token)
            continue
        if preservar_prestamos and _es_prestamo(token):
            salida.append(token)
            continue

        base = token.lower()

        # Orden critico: las grafias hispanizantes se resuelven ANTES de la
        # conversion vocalica, porque sus reglas dependen de las vocales e/o
        # originales. Invertir el orden destruye secuencias legitimas: "qosqo"
        # pasaria a "qusqu" y luego un reemplazo ciego de "qu" daria "ksk".
        base = re.sub(r"hu(?=[aeiou])", "w", base)   # huahua -> wawa
        base = re.sub(r"qu(?=[ei])", "k", base)      # quechua -> kechua (no toca qusqu)
        base = re.sub(r"c(?=[ei])", "s", base)       # cielo -> sielo
        base = re.sub(r"c(?=[aou])", "k", base)      # casa -> kasa
        base = base.replace("z", "s").replace("v", "w").replace("x", "s")

        # Sistema trivocalico oficial: e/o son alofonos de i/u ante /q/.
        base = base.replace("e", "i").replace("o", "u")

        salida.append(_aplicar_caso(token, base))

    return "".join(salida)


def validar_alfabeto(texto: str) -> list[str]:
    """Devuelve las grafias presentes que no pertenecen al alfabeto oficial."""
    plano = unicodedata.normalize("NFC", texto.lower())
    permitidas = set("aiuchhqptkmnñlrswy' -\n\t")
    return sorted({c for c in plano if c.isalpha() and c not in permitidas})


__all__ = [
    "PerfilDialectal",
    "detectar_variante",
    "normalizar_trivocalico",
    "validar_alfabeto",
    "GRAFIAS_OFICIALES",
    "VOCALES_OFICIALES",
]
