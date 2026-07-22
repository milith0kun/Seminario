// Puerto de src/rag/indice_bm25.py (BM25Okapi, k1=1.5, b=0.75, epsilon=0.25 — mismos
// valores por defecto que la librería Python rank_bm25 usada en el backend original)

export interface Chunk {
  chunk_id: string;
  source_id: string;
  text: string;
  tokens_estimated?: number;
  language?: string;
  dialect?: string;
  domain?: string;
  grade?: string;
  source_ref?: string;
  title?: string;
}

export interface ChunkConScore extends Chunk {
  score: number;
}

export function tokenize(text: string): string[] {
  return text.toLowerCase().match(/[A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9']+/g) ?? [];
}

const K1 = 1.5;
const B = 0.75;
const EPSILON = 0.25;

export class BM25Index {
  chunks: Chunk[];
  private corpus: string[][];
  private corpusSize = 0;
  private avgdl = 0;
  private docFreqs: Map<string, number>[] = [];
  private docLen: number[] = [];
  private idf = new Map<string, number>();

  constructor(chunks: Chunk[]) {
    this.chunks = chunks;
    this.corpus = chunks.map((c) => tokenize(c.text ?? ''));
    if (chunks.length > 0) {
      this.initialize();
    }
  }

  static async fromUrl(url: string): Promise<BM25Index> {
    const res = await fetch(url);
    const text = await res.text();
    const chunks: Chunk[] = text
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .map((line) => JSON.parse(line));
    return new BM25Index(chunks);
  }

  private initialize(): void {
    const nd = new Map<string, number>();
    let numDoc = 0;

    for (const document of this.corpus) {
      this.docLen.push(document.length);
      numDoc += document.length;

      const frequencies = new Map<string, number>();
      for (const word of document) {
        frequencies.set(word, (frequencies.get(word) ?? 0) + 1);
      }
      this.docFreqs.push(frequencies);

      for (const word of frequencies.keys()) {
        nd.set(word, (nd.get(word) ?? 0) + 1);
      }

      this.corpusSize += 1;
    }

    this.avgdl = numDoc / this.corpusSize;
    this.calcIdf(nd);
  }

  private calcIdf(nd: Map<string, number>): void {
    let idfSum = 0;
    const negativeIdfs: string[] = [];
    for (const [word, freq] of nd.entries()) {
      const idf = Math.log(this.corpusSize - freq + 0.5) - Math.log(freq + 0.5);
      this.idf.set(word, idf);
      idfSum += idf;
      if (idf < 0) {
        negativeIdfs.push(word);
      }
    }
    const averageIdf = idfSum / this.idf.size;
    const eps = EPSILON * averageIdf;
    for (const word of negativeIdfs) {
      this.idf.set(word, eps);
    }
  }

  private getScores(query: string[]): number[] {
    const scores = new Array(this.corpusSize).fill(0);
    for (const q of query) {
      const idf = this.idf.get(q) ?? 0;
      if (idf === 0) continue;
      for (let i = 0; i < this.corpusSize; i++) {
        const qFreq = this.docFreqs[i].get(q) ?? 0;
        const docLen = this.docLen[i];
        scores[i] +=
          idf * ((qFreq * (K1 + 1)) / (qFreq + K1 * (1 - B + (B * docLen) / this.avgdl)));
      }
    }
    return scores;
  }

  search(query: string, topK = 5): ChunkConScore[] {
    if (this.corpusSize === 0) {
      return [];
    }
    const scores = this.getScores(tokenize(query));
    const ranked = scores
      .map((score, idx) => ({ idx, score }))
      .sort((a, b) => b.score - a.score)
      .slice(0, topK);
    return ranked.map(({ idx, score }) => ({ ...this.chunks[idx], score }));
  }
}
