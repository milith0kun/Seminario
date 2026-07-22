import Fuse from "fuse.js";

export interface ChunkRAG {
  chunk_id: string;
  source_id: string;
  title: string;
  language: string;
  dialect: string;
  text: string;
}

export interface HitRAG {
  chunk: ChunkRAG;
  score: number;
}

let fuseInstance: Fuse<ChunkRAG> | null = null;
let cachedChunks: ChunkRAG[] = [];

export async function cargarChunksLocal(): Promise<ChunkRAG[]> {
  if (cachedChunks.length > 0) return cachedChunks;
  try {
    const res = await fetch("/chunks.json");
    if (!res.ok) return [];
    cachedChunks = await res.json();
    fuseInstance = new Fuse(cachedChunks, {
      keys: ["title", "text", "dialect", "language"],
      threshold: 0.4,
      includeScore: true,
    });
    return cachedChunks;
  } catch (err) {
    console.error("Error cargando chunks RAG en cliente:", err);
    return [];
  }
}

export async function buscarRAGLocal(pregunta: string, topK: number = 3): Promise<HitRAG[]> {
  if (!fuseInstance) {
    await cargarChunksLocal();
  }
  if (!fuseInstance) return [];

  const results = fuseInstance.search(pregunta, { limit: topK });
  return results.map((r) => ({
    chunk: r.item,
    score: 1 - (r.score ?? 0.5),
  }));
}

export function construirContextoRAG(hits: HitRAG[]): string {
  if (hits.length === 0) return "";
  return hits
    .map(
      (h, idx) =>
        `[Documento ${idx + 1}: ${h.chunk.title} (${h.chunk.language}/${h.chunk.dialect})]\n${h.chunk.text}`
    )
    .join("\n\n");
}
