"""FASE 2 - Motor RAG vectorial con embeddings densos y distancia de coseno.

Implementa la recuperacion curricular del Escenario E2/E3:

    sim(q, d) = (e_q . e_d) / (||e_q|| ||e_d||)

Los vectores se normalizan a norma unitaria en el momento de la codificacion,
de modo que la similitud de coseno se reduce a un producto punto y el indice
completo se resuelve con una sola multiplicacion matricial.

El modelo de embeddings se carga desde disco (multilingual-e5-small) para que
todo el pipeline sea reproducible sin acceso a red.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

# e5 exige prefijos de rol; omitirlos degrada notablemente la recuperacion.
PREFIJO_CONSULTA = "query: "
PREFIJO_PASAJE = "passage: "

TOP_K_POR_DEFECTO = 3
UMBRAL_POR_DEFECTO = 0.65

# Guardarrail de cobertura lexica.
#
# El umbral de coseno por si solo NO detecta consultas sin respaldo: e5 es
# anisotropico y comprime las similitudes en una banda alta y estrecha. Medido
# sobre las 100 consultas de evaluacion, la similitud maxima fue 0.821-0.919
# para consultas con respaldo y 0.837-0.870 para las sondas de alucinacion:
# las distribuciones se solapan y ningun corte absoluto las separa.
#
# La cobertura lexica (fraccion de terminos de contenido de la consulta que
# existen en el vocabulario del corpus) si discrimina, porque las consultas sin
# respaldo piden entidades ausentes -codigos de resolucion, numeros de pagina,
# porcentajes-. Distribucion medida: mediana 0.667 con respaldo frente a 0.222
# en las sondas. El corte 0.30 maximiza el indice de Youden (J=0.875):
# conserva el 100% de las consultas con respaldo y descarta el 87.5% de las
# sondas. BM25 se descarto: puntua MAS alto en las sondas (30.1 frente a 19.9),
# porque estas acumulan terminos genericos frecuentes.
UMBRAL_COBERTURA_LEXICA = 0.30

_RE_PALABRA = re.compile(r"[^\W\d_]+", re.UNICODE)

# Terminos funcionales que no aportan evidencia de anclaje al corpus.
_VACIAS = frozenset(
    """
    que como cual cuales quien donde cuando cuanto cuantos cuanta cuantas por
    para del las los una unos unas con sin sobre segun mas muy este esta esto
    esos esas ese esa aquel aquella son ser esta estan hay tiene tienen en el
    la de y a o u al se lo le su sus me te nos dentro area contexto significa
    dice sobre entre desde hasta ante bajo entonces tambien entiende explica
    """.split()
)


@dataclass
class FragmentoRecuperado:
    chunk_id: str
    titulo: str
    area: str
    grado: str
    contenido_es: str
    contenido_qu: str
    referencia: str
    origen: str
    similitud: float

    def texto_para_contexto(self) -> str:
        partes = []
        if self.contenido_es:
            partes.append(f"Espanol: {self.contenido_es}")
        if self.contenido_qu:
            partes.append(f"Quechua Collao: {self.contenido_qu}")
        return "\n".join(partes)


@dataclass
class ResultadoRecuperacion:
    consulta: str
    fragmentos: list[FragmentoRecuperado] = field(default_factory=list)
    latencia_ms: float = 0.0
    similitud_maxima: float = 0.0
    bajo_umbral: bool = False
    cobertura_lexica: float = 0.0
    sin_respaldo: bool = False

    @property
    def hubo_recuperacion(self) -> bool:
        return bool(self.fragmentos)


class IndiceVectorial:
    """Indice denso de fragmentos curriculares con busqueda por coseno."""

    def __init__(
        self,
        fragmentos: list[dict[str, Any]],
        matriz: np.ndarray,
        modelo_id: str,
        modelo=None,
    ) -> None:
        self.fragmentos = fragmentos
        self.matriz = matriz  # (n_fragmentos, dim), filas de norma 1
        self.modelo_id = modelo_id
        self._modelo = modelo
        self._vocabulario = self._construir_vocabulario(fragmentos)

    @staticmethod
    def _construir_vocabulario(fragmentos: list[dict[str, Any]]) -> set[str]:
        vocab: set[str] = set()
        for f in fragmentos:
            vocab.update(_RE_PALABRA.findall(IndiceVectorial._texto_indexable(f).lower()))
        return vocab

    def cobertura_lexica(self, consulta: str) -> float:
        """Fraccion de terminos de contenido de la consulta presentes en el corpus."""
        terminos = [
            t for t in _RE_PALABRA.findall(consulta.lower())
            if t not in _VACIAS and len(t) > 3
        ]
        if not terminos:
            return 1.0  # Sin terminos de contenido no hay evidencia de vacio.
        return sum(1 for t in terminos if t in self._vocabulario) / len(terminos)

    # -- construccion --------------------------------------------------

    @staticmethod
    def _texto_indexable(fragmento: dict[str, Any]) -> str:
        partes = [
            fragmento.get("titulo", ""),
            fragmento.get("area", ""),
            fragmento.get("contenido_es", ""),
            fragmento.get("contenido_qu", ""),
            " ".join(fragmento.get("palabras_clave_es") or []),
            " ".join(fragmento.get("palabras_clave_qu") or []),
        ]
        return " ".join(p for p in partes if p).strip()

    @classmethod
    def construir(
        cls,
        fragmentos: list[dict[str, Any]],
        ruta_modelo: Path,
        *,
        batch_size: int = 16,
    ) -> "IndiceVectorial":
        from sentence_transformers import SentenceTransformer

        modelo = SentenceTransformer(str(ruta_modelo), device="cpu")
        textos = [PREFIJO_PASAJE + cls._texto_indexable(f) for f in fragmentos]
        matriz = modelo.encode(
            textos,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)
        return cls(fragmentos, matriz, str(ruta_modelo), modelo)

    # -- persistencia --------------------------------------------------

    def guardar(self, directorio: Path) -> None:
        directorio.mkdir(parents=True, exist_ok=True)
        np.save(directorio / "embeddings.npy", self.matriz)
        with (directorio / "fragmentos.jsonl").open("w", encoding="utf-8") as f:
            for fragmento in self.fragmentos:
                f.write(json.dumps(fragmento, ensure_ascii=False) + "\n")
        (directorio / "indice_meta.json").write_text(
            json.dumps(
                {
                    "modelo_embeddings": self.modelo_id,
                    "n_fragmentos": len(self.fragmentos),
                    "dimension": int(self.matriz.shape[1]),
                    "metrica": "coseno (producto punto sobre vectores normalizados)",
                    "prefijo_consulta": PREFIJO_CONSULTA,
                    "prefijo_pasaje": PREFIJO_PASAJE,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    @classmethod
    def cargar(cls, directorio: Path, ruta_modelo: Path | None = None) -> "IndiceVectorial":
        matriz = np.load(directorio / "embeddings.npy")
        fragmentos = [
            json.loads(l)
            for l in (directorio / "fragmentos.jsonl").read_text(encoding="utf-8").splitlines()
            if l.strip()
        ]
        meta = json.loads((directorio / "indice_meta.json").read_text(encoding="utf-8"))
        modelo_id = str(ruta_modelo) if ruta_modelo else meta["modelo_embeddings"]

        from sentence_transformers import SentenceTransformer

        modelo = SentenceTransformer(modelo_id, device="cpu")
        return cls(fragmentos, matriz, modelo_id, modelo)

    # -- recuperacion --------------------------------------------------

    def recuperar(
        self,
        consulta: str,
        top_k: int = TOP_K_POR_DEFECTO,
        umbral: float = UMBRAL_POR_DEFECTO,
        umbral_cobertura: float = UMBRAL_COBERTURA_LEXICA,
    ) -> ResultadoRecuperacion:
        inicio = time.perf_counter()
        if self._modelo is None:
            raise RuntimeError("El indice no tiene modelo de embeddings cargado.")

        # Guardarrail previo: si la consulta pide entidades que no existen en el
        # corpus, se declara sin respaldo y no se inyecta contexto. Inyectar los
        # fragmentos mas cercanos en ese caso solo aportaria material irrelevante
        # sobre el que el modelo tenderia a construir una respuesta inventada.
        cobertura = self.cobertura_lexica(consulta)
        if cobertura < umbral_cobertura:
            return ResultadoRecuperacion(
                consulta=consulta,
                fragmentos=[],
                latencia_ms=(time.perf_counter() - inicio) * 1000,
                similitud_maxima=0.0,
                bajo_umbral=True,
                cobertura_lexica=cobertura,
                sin_respaldo=True,
            )

        vector = self._modelo.encode(
            [PREFIJO_CONSULTA + consulta],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)[0]

        # Ambos lados estan normalizados: el producto punto ES el coseno.
        similitudes = self.matriz @ vector
        orden = np.argsort(-similitudes)[:top_k]

        similitud_maxima = float(similitudes[orden[0]]) if len(orden) else 0.0
        fragmentos: list[FragmentoRecuperado] = []
        for idx in orden:
            score = float(similitudes[idx])
            if score < umbral:
                continue
            f = self.fragmentos[int(idx)]
            fragmentos.append(
                FragmentoRecuperado(
                    chunk_id=f.get("chunk_id", ""),
                    titulo=f.get("titulo", ""),
                    area=f.get("area", ""),
                    grado=f.get("grado", ""),
                    contenido_es=f.get("contenido_es", ""),
                    contenido_qu=f.get("contenido_qu", ""),
                    referencia=f.get("referencia", ""),
                    origen=f.get("origen", ""),
                    similitud=score,
                )
            )

        return ResultadoRecuperacion(
            consulta=consulta,
            fragmentos=fragmentos,
            latencia_ms=(time.perf_counter() - inicio) * 1000,
            similitud_maxima=similitud_maxima,
            bajo_umbral=not fragmentos,
            cobertura_lexica=cobertura,
            sin_respaldo=not fragmentos,
        )


__all__ = [
    "IndiceVectorial",
    "FragmentoRecuperado",
    "ResultadoRecuperacion",
    "TOP_K_POR_DEFECTO",
    "UMBRAL_POR_DEFECTO",
    "UMBRAL_COBERTURA_LEXICA",
]
