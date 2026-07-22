"use client";

import log from "loglevel";
// Importar desde "@wllama/wllama" (el índice raíz del paquete) resuelve a
// los .ts fuente sin compilar y rompe el build de Next — hay que apuntar
// directo al bundle ESM ya compilado.
import { Wllama, type WllamaChatMessage } from "@wllama/wllama/esm/index.js";

import { ChatOptions, LLMApi, LLMConfig, RequestMessage } from "./api";
import { fixMessage, extraerMensajeError } from "../utils";
import { DEFAULT_WLLAMA_MODELS, WLLAMA_MODEL_SOURCES } from "../constant";
import { buscarRAGLocal, construirContextoRAG } from "../rag";

const MAX_TOKENS_CPU = 512; // respuestas más cortas: la inferencia por CPU es lenta

// El helper "wasm-from-cdn.js" del paquete no incluye el .js real en esta
// versión (solo el .d.ts) — falla el build. En vez de depender de esa CDN,
// se copió el único wllama.wasm que trae el paquete (single-thread; no
// incluye build multi-hilo) a public/wllama/ y se sirve como asset
// estático, sin pasar por el bundler de webpack.
const WLLAMA_ASSET_PATHS = {
  default: "/wllama/wllama.wasm",
};

export class WllamaApi implements LLMApi {
  private wllama: Wllama;
  private llmConfig?: LLMConfig;
  private initialized = false;
  private abortController: AbortController | null = null;

  constructor(logLevel: string = "WARN") {
    this.wllama = new Wllama(WLLAMA_ASSET_PATHS, {
      suppressNativeLog: logLevel !== "DEBUG",
    });
  }

  private async initModel(onUpdate?: (message: string, chunk: string) => void) {
    if (!this.llmConfig) {
      throw new Error("llmConfig is undefined");
    }
    const source = WLLAMA_MODEL_SOURCES[this.llmConfig.model];
    if (!source) {
      throw new Error(
        `Modelo CPU desconocido: ${this.llmConfig.model} (no está en WLLAMA_MODEL_SOURCES)`,
      );
    }

    const startedAt = Date.now();
    let descargaCompleta = false;

    // loadModelFromHF no avisa nada mientras vuelca el archivo (~1-2 GB) a
    // la memoria del WASM de un solo hilo, paso que puede tardar varios
    // minutos en un celular. Sin este ticker, la barra quedaría fija en
    // "100%" apenas termina la descarga y parecería que la app se colgó.
    const ticker = setInterval(() => {
      if (!descargaCompleta) return;
      const secs = Math.round((Date.now() - startedAt) / 1000);
      const text =
        "Modelo descargado. Preparando en memoria (puede tardar varios " +
        `minutos en un celular), ${secs} segs transcurridos...`;
      onUpdate?.(text, text);
    }, 2_000);

    try {
      await this.wllama.loadModelFromHF(
        { repo: source.repo, file: source.file },
        {
          progressCallback: ({ loaded, total }) => {
            const pct = total ? Math.floor((loaded / total) * 100) : 0;
            const secs = Math.round((Date.now() - startedAt) / 1000);
            if (pct >= 100) {
              descargaCompleta = true;
              return;
            }
            const text = `Descargando modelo (CPU): ${pct}% completed, ${secs} secs elapsed.`;
            onUpdate?.(text, text);
          },
        },
      );
    } finally {
      clearInterval(ticker);
    }
    this.initialized = true;
  }

  async chat(options: ChatOptions): Promise<void> {
    if (!this.initialized || this.isDifferentConfig(options.config)) {
      this.llmConfig = { ...(this.llmConfig || {}), ...options.config };
      try {
        await this.initModel(options.onUpdate);
      } catch (err: any) {
        const errorMessage = extraerMensajeError(err);
        log.error("Error al inicializar el modelo CPU (wllama)", errorMessage);
        options?.onError?.(new Error(errorMessage));
        return;
      }
    }

    let reply = "";
    try {
      reply = await this.chatCompletion(
        options.messages,
        options.onUpdate,
        options.config,
      );
    } catch (err: any) {
      const errorMessage = extraerMensajeError(err);
      log.error("Error en chatCompletion (wllama/CPU)", errorMessage);
      // Igual que con el motor GPU: si la generación falla, forzamos
      // reinicialización en el próximo intento en vez de asumir que el
      // modelo sigue cargado.
      this.initialized = false;
      options.onError?.(new Error(errorMessage));
      return;
    }

    if (reply) {
      options.onFinish(fixMessage(reply), "stop", undefined);
    } else {
      options.onError?.(new Error("Respuesta vacía del modelo (CPU)"));
    }
  }

  async abort() {
    this.abortController?.abort();
  }

  private isDifferentConfig(config: LLMConfig): boolean {
    return !this.llmConfig || this.llmConfig.model !== config.model;
  }

  private async chatCompletion(
    messages: RequestMessage[],
    onUpdate: ((message: string, chunk: string) => void) | undefined,
    config: LLMConfig,
  ): Promise<string> {
    // Inyección de RAG local: mismo mecanismo que usa el motor GPU
    // (WebLLMApi), reutilizando las mismas funciones de ../rag.
    const finalMessages = messages.map((m) => ({ ...m }));
    const lastUserMsg = finalMessages.filter((m) => m.role === "user").pop();
    if (lastUserMsg && typeof lastUserMsg.content === "string") {
      try {
        const hits = await buscarRAGLocal(lastUserMsg.content, 3);
        if (hits.length > 0) {
          const contextStr = construirContextoRAG(hits);
          const ragPrompt = `\n\n[CONTEXTO DOCUMENTAL RAG RELEVANTE RECUPERADO DE LA BASE EIB]:\n${contextStr}\n\nUsa la información anterior para responder de forma precisa al usuario.`;
          lastUserMsg.content = lastUserMsg.content + ragPrompt;
        }
      } catch (err) {
        log.warn("Fallo al buscar RAG en cliente (CPU):", err);
      }
    }

    const wllamaMessages: WllamaChatMessage[] = finalMessages.map((m) => ({
      role: m.role,
      content:
        typeof m.content === "string" ? m.content : JSON.stringify(m.content),
    }));

    this.abortController = new AbortController();

    const chunks = await this.wllama.createChatCompletion({
      messages: wllamaMessages,
      stream: true,
      temperature: config.temperature,
      top_p: config.top_p,
      // Sin esto el modelo (sobre todo el 0.5B, más propenso a degenerar)
      // puede repetirse o producir texto incoherente/cortado. Son los
      // valores por defecto recomendados en la documentación de wllama.
      top_k: 40,
      penalty_repeat: 1.1,
      max_tokens: MAX_TOKENS_CPU,
      abortSignal: this.abortController.signal,
    });

    let content = "";
    for await (const chunk of chunks) {
      const delta = chunk.choices[0]?.delta?.content;
      if (delta) {
        content += delta;
        onUpdate?.(content, delta);
      }
    }
    return content;
  }

  async models() {
    return DEFAULT_WLLAMA_MODELS;
  }
}
