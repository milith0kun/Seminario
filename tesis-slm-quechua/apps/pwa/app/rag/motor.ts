// Orquestación local de RAG + enrutamiento de idioma para el asistente EIB.
// Se ejecuta 100% en el cliente: el corpus se carga una sola vez desde
// /rag/chunks.jsonl y el índice BM25 se mantiene en memoria del navegador.

import { BM25Index, ChunkConScore } from "./indiceBm25";
import { buildContext } from "./constructorContexto";
import { detectLanguage, IdiomaDetectado } from "./enrutadorLenguaje";

const CHUNKS_URL = "/rag/chunks.jsonl";
const TOP_K = 3;
const MAX_CHUNKS_CONTEXTO = 3;

let indicePromise: Promise<BM25Index> | null = null;

function cargarIndice(): Promise<BM25Index> {
  if (!indicePromise) {
    indicePromise = BM25Index.fromUrl(CHUNKS_URL).catch((err) => {
      indicePromise = null;
      throw err;
    });
  }
  return indicePromise;
}

// Precarga el índice apenas se importa este módulo en el cliente, para que
// la primera pregunta del usuario no tenga que esperar el fetch del corpus.
if (typeof window !== "undefined") {
  cargarIndice().catch(() => {
    /* se reintenta en el siguiente augmentarPregunta */
  });
}

export interface ResultadoAugmentacion {
  contenido: string;
  idioma: IdiomaDetectado;
  ragHits: ChunkConScore[];
}

function sufijoIdioma(idioma: IdiomaDetectado): string {
  if (idioma === "qu_collao") {
    return "\n\n[Instrucción de idioma: prioriza Quechua Collao en la respuesta.]";
  }
  if (idioma === "mixed_es_qu") {
    return "\n\n[Instrucción de idioma: puedes combinar español y Quechua Collao con claridad.]";
  }
  return "";
}

export async function augmentarPregunta(
  pregunta: string,
): Promise<ResultadoAugmentacion> {
  const idioma = detectLanguage(pregunta);

  let ragHits: ChunkConScore[] = [];
  try {
    const indice = await cargarIndice();
    ragHits = indice.search(pregunta, TOP_K);
  } catch (err) {
    console.warn("[RAG] No se pudo cargar/consultar el índice BM25:", err);
  }

  const contexto = ragHits.length > 0 ? buildContext(ragHits, MAX_CHUNKS_CONTEXTO) : "";

  let contenido = pregunta;
  if (contexto) {
    contenido = `Contexto:\n${contexto}\n\nConsulta del estudiante:\n${pregunta}`;
  }
  contenido += sufijoIdioma(idioma);

  return { contenido, idioma, ragHits };
}
