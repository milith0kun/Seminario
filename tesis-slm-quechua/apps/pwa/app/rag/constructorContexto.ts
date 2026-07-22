// Puerto literal de src/rag/constructor_contexto.py

import { ChunkConScore } from './indiceBm25';

export function buildContext(chunks: ChunkConScore[], maxChunks = 5): string {
  const parts: string[] = [];
  chunks.slice(0, maxChunks).forEach((c, i) => {
    const sid = c.source_id ?? '?';
    const ref = c.source_ref ?? '';
    const text = (c.text ?? '').trim();
    parts.push(`[${i + 1}] source=${sid} ref=${ref}\n${text}`);
  });
  return parts.join('\n\n');
}
