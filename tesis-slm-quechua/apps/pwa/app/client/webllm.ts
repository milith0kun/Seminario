"use client";

import log from "loglevel";
import { createContext } from "react";
import {
  InitProgressReport,
  prebuiltAppConfig,
  ChatCompletionMessageParam,
  ServiceWorkerMLCEngine,
  ChatCompletionChunk,
  ChatCompletion,
  WebWorkerMLCEngine,
  CompletionUsage,
  ChatCompletionFinishReason,
  deleteModelAllInfoInCache,
} from "@mlc-ai/web-llm";

import { ChatOptions, LLMApi, LLMConfig, RequestMessage } from "./api";
import { LogLevel } from "@mlc-ai/web-llm";
import { fixMessage, extraerMensajeError } from "../utils";
import { DEFAULT_MODELS } from "../constant";
import { buscarRAGLocal, construirContextoRAG } from "../rag";


const KEEP_ALIVE_INTERVAL = 5_000;

type ServiceWorkerWebLLMHandler = {
  type: "serviceWorker";
  engine: ServiceWorkerMLCEngine;
};

type WebWorkerWebLLMHandler = {
  type: "webWorker";
  engine: WebWorkerMLCEngine;
};

type WebLLMHandler = ServiceWorkerWebLLMHandler | WebWorkerWebLLMHandler;

export class WebLLMApi implements LLMApi {
  private llmConfig?: LLMConfig;
  private initialized = false;
  webllm: WebLLMHandler;

  constructor(
    type: "serviceWorker" | "webWorker",
    logLevel: LogLevel = "WARN",
    // OJO: no leer `this.llmConfig?.cache` acá — en este punto del
    // constructor `this.llmConfig` todavía no se asignó (eso pasa recién
    // en `chat()`), así que siempre daba `undefined` y este ajuste de
    // Settings ("tipo de caché") no tenía ningún efecto real. Se recibe
    // ya resuelto desde quien crea la instancia (useWebLLM en home.tsx),
    // que sí conoce el `cacheType` configurado.
    useIndexedDBCache: boolean = false,
  ) {
    const engineConfig = {
      appConfig: {
        ...prebuiltAppConfig,
        useIndexedDBCache,
      },
      logLevel,
    };

    if (type === "serviceWorker") {
      log.info("Create ServiceWorkerMLCEngine");
      this.webllm = {
        type: "serviceWorker",
        engine: new ServiceWorkerMLCEngine(engineConfig, KEEP_ALIVE_INTERVAL),
      };
    } else {
      log.info("Create WebWorkerMLCEngine");
      this.webllm = {
        type: "webWorker",
        engine: new WebWorkerMLCEngine(
          new Worker(new URL("../worker/web-worker.ts", import.meta.url), {
            type: "module",
          }),
          engineConfig,
        ),
      };
    }
  }

  private async initModel(onUpdate?: (message: string, chunk: string) => void) {
    if (!this.llmConfig) {
      throw Error("llmConfig is undefined");
    }
    this.webllm.engine.setInitProgressCallback((report: InitProgressReport) => {
      onUpdate?.(report.text, report.text);
    });
    await this.webllm.engine.reload(this.llmConfig.model, this.llmConfig);
    this.initialized = true;
  }

  async chat(options: ChatOptions): Promise<void> {
    if (!this.initialized || this.isDifferentConfig(options.config)) {
      this.llmConfig = { ...(this.llmConfig || {}), ...options.config };
      // Check if this is a Qwen3 model with thinking mode enabled
      const isQwen3Model = this.llmConfig?.model
        ?.toLowerCase()
        .startsWith("qwen3");
      const isThinkingEnabled = this.llmConfig?.enable_thinking === true;

      // Apply special config for Qwen3 models with thinking mode enabled
      if (isQwen3Model && isThinkingEnabled && this.llmConfig) {
        this.llmConfig = {
          ...this.llmConfig,
          temperature: 0.6,
          top_p: 0.95,
        };
      }
      try {
        await this.initModel(options.onUpdate);
      } catch (err: any) {
        const errorMessage = extraerMensajeError(err);
        console.error("Error while initializing the model", errorMessage);
        options?.onError?.(new Error(errorMessage));
        return;
      }
    }

    let reply: string | null = "";
    let stopReason: ChatCompletionFinishReason | undefined;
    let usage: CompletionUsage | undefined;
    try {
      const completion = await this.chatCompletion(
        !!options.config.stream,
        options.messages,
        options.onUpdate,
      );
      reply = completion.content;
      stopReason = completion.stopReason;
      usage = completion.usage;
    } catch (err: any) {
      let errorMessage = extraerMensajeError(err);
      console.error("Error in chatCompletion", errorMessage);
      if (
        errorMessage.includes("WebGPU") &&
        errorMessage.includes("compatibility chart")
      ) {
        // Add WebGPU compatibility chart link
        errorMessage = errorMessage.replace(
          "compatibility chart",
          "[compatibility chart](https://caniuse.com/webgpu)",
        );
      }
      // Si la generación falla (ej. GPUPipelineError por caché de shaders
      // inválida), el engine puede quedar en un estado roto aunque
      // `initModel()` haya terminado bien antes. Sin este reset, el
      // siguiente mensaje se envía sin recargar el modelo y falla con
      // "ModelNotLoadedError". Forzamos un reload en el próximo intento.
      this.initialized = false;

      if (
        /ShaderModule|GPUPipelineError|reshape.*_kernel/i.test(errorMessage) &&
        this.llmConfig?.model
      ) {
        // La causa más común de este error es una caché de pesos/wasm
        // corrupta (ej. una descarga que se cortó a mitad). Cambiar de
        // motor no ayuda porque ambos leen la misma caché del navegador.
        // Se borra la caché de este modelo para forzar una descarga limpia
        // la próxima vez.
        try {
          await deleteModelAllInfoInCache(this.llmConfig.model, {
            ...prebuiltAppConfig,
            useIndexedDBCache: this.llmConfig.cache === "index_db",
          });
          log.info(
            `Caché borrada para ${this.llmConfig.model} tras error de GPU.`,
          );
        } catch (cacheErr) {
          console.warn("No se pudo borrar la caché del modelo:", cacheErr);
        }
      }

      options.onError?.(new Error(errorMessage));
      return;
    }

    if (reply) {
      reply = fixMessage(reply);
      options.onFinish(reply, stopReason, usage);
    } else {
      options.onError?.(new Error("Empty response generated by LLM"));
    }
  }

  async abort() {
    await this.webllm.engine?.interruptGenerate();
  }

  private isDifferentConfig(config: LLMConfig): boolean {
    if (!this.llmConfig) {
      return true;
    }

    // Compare required fields
    if (this.llmConfig.model !== config.model) {
      return true;
    }

    // Compare optional fields
    const optionalFields: (keyof LLMConfig)[] = [
      "temperature",
      "context_window_size",
      "top_p",
      "stream",
      "presence_penalty",
      "frequency_penalty",
      "enable_thinking",
    ];

    for (const field of optionalFields) {
      if (
        this.llmConfig[field] !== undefined &&
        config[field] !== undefined &&
        this.llmConfig[field] !== config[field]
      ) {
        return true;
      }
    }

    return false;
  }

  async chatCompletion(
    stream: boolean,
    messages: RequestMessage[],
    onUpdate?: (
      message: string,
      chunk: string,
      usage?: CompletionUsage,
    ) => void,
  ) {
    // For Qwen3 models, we need to filter out the <think>...</think> content
    // Do not do it inplace, create a new messages array
    let newMessages: RequestMessage[] | undefined;
    const isQwen3Model = this.llmConfig?.model
      ?.toLowerCase()
      .startsWith("qwen3");
    if (isQwen3Model) {
      newMessages = messages.map((message) => {
        const newMessage = { ...message };
        if (
          message.role === "assistant" &&
          typeof message.content === "string"
        ) {
          newMessage.content = message.content.replace(
            /^<think>[\s\S]*?<\/think>\n?\n?/,
            "",
          );
        }
        return newMessage;
      });
    }

    // Prepare extra_body with enable_thinking option for Qwen3 models
    const extraBody: Record<string, any> = {};
    if (isQwen3Model) {
      extraBody.enable_thinking = this.llmConfig?.enable_thinking ?? false;
    }

    // Inyección de RAG local en cliente
    let finalMessages = newMessages || [...messages];
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
        console.warn("Fallo al buscar RAG en cliente:", err);
      }
    }

    const completion = await this.webllm.engine.chatCompletion({
      stream: stream,
      messages: finalMessages as ChatCompletionMessageParam[],
      ...(stream ? { stream_options: { include_usage: true } } : {}),
      ...(Object.keys(extraBody).length > 0 ? { extra_body: extraBody } : {}),
    });


    if (stream) {
      let content: string | null = "";
      let stopReason: ChatCompletionFinishReason | undefined;
      let usage: CompletionUsage | undefined;
      const asyncGenerator = completion as AsyncIterable<ChatCompletionChunk>;
      for await (const chunk of asyncGenerator) {
        if (chunk.choices[0]?.delta.content) {
          content += chunk.choices[0].delta.content;
          onUpdate?.(content, chunk.choices[0].delta.content);
        }
        if (chunk.usage) {
          usage = chunk.usage;
        }
        if (chunk.choices[0]?.finish_reason) {
          stopReason = chunk.choices[0].finish_reason;
        }
      }
      return { content, stopReason, usage };
    }

    const chatCompletion = completion as ChatCompletion;
    return {
      content: chatCompletion.choices[0].message.content,
      stopReason: chatCompletion.choices[0].finish_reason,
      usage: chatCompletion.usage,
    };
  }

  async models() {
    return DEFAULT_MODELS;
  }
}
