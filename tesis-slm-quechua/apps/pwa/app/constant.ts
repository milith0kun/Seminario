import { prebuiltAppConfig } from "@mlc-ai/web-llm";
import { ModelRecord } from "./client/api";
import { getQuantization, getSize } from "./utils";

export const OWNER = "mlc-ai";
export const REPO = "web-llm-chat";
export const WEBLLM_HOME_URL = "https://webllm.mlc.ai";
export const REPO_URL = `https://github.com/${OWNER}/${REPO}`;
export const ISSUE_URL = `https://github.com/${OWNER}/${REPO}/issues`;

export enum Path {
  Home = "/",
  Chat = "/chat",
  Settings = "/settings",
  Templates = "/templates",
}

export enum ApiPath {
  Cors = "",
}

export enum SlotID {
  AppBody = "app-body",
  CustomModel = "custom-model",
}

export enum FileName {
  Templates = "templates.json",
  Prompts = "prompts.json",
}

export enum StoreKey {
  Chat = "chat-next-web-store",
  Access = "access-control",
  Config = "app-config",
  Templates = "templates-store",
  Prompt = "prompt-store",
  Update = "chat-update",
  Sync = "sync",
}

export const DEFAULT_SIDEBAR_WIDTH = 320;
export const MAX_SIDEBAR_WIDTH = 500;
export const MIN_SIDEBAR_WIDTH = 260;
export const NARROW_SIDEBAR_WIDTH = 100;

export const ACCESS_CODE_PREFIX = "nk-";

export const LAST_INPUT_KEY = "last-input";
export const UNFINISHED_INPUT = (name: string) => "unfinished-input-" + name;

export const STORAGE_KEY = "chatgpt-next-web";

export const REQUEST_TIMEOUT_MS = 60000;

export const EXPORT_MESSAGE_CLASS_NAME = "export-markdown";

// Si el motor hospedado en el Service Worker queda en un estado de GPU
// corrupto (ej. GPUPipelineError con shaders inválidos), un simple F5 NO
// lo arregla: el Service Worker sigue vivo en segundo plano entre
// recargas de página, así que el mismo GPUDevice roto persiste. Cuando se
// detecta ese error, se guarda esta bandera para que la próxima carga use
// un WebWorker (que sí se destruye y recrea con cada recarga de página,
// obteniendo un GPUDevice nuevo).
export const FORZAR_WEBWORKER_KEY = "eib-forzar-webworker";

// Cuando ni Service Worker ni WebWorker logran correr el modelo por GPU
// (dispositivo sin WebGPU utilizable), se guarda esta bandera para pasar
// al motor CPU (wllama/WASM) de forma automática y permanente en este
// dispositivo — no depende de la GPU en absoluto, así que sirve como
// último respaldo para que la app funcione en cualquier celular/PC.
export const FORZAR_CPU_KEY = "eib-forzar-cpu";

export const DEFAULT_INPUT_TEMPLATE = `{{input}}`; // input / time / model / lang

// Puerto literal de SYSTEM_WITH_CONTEXT en src/inferencia/plantillas_prompt.py
export const DEFAULT_SYSTEM_TEMPLATE = `
Eres un asistente educativo para Educacion Intercultural Bilingue (EIB). Responde de forma clara, breve y con andamiaje: guia al estudiante sin dar solo la respuesta final. Usa espanol o Quechua Collao segun la consulta. Si no sabes, dilo. No inventes hechos curriculares. Usa solo el contexto recuperado cuando exista. Cita la fuente si aparece.
Model display_name: {{model}}
`;

export enum ModelFamily {
  LLAMA = "llama",
  PHI = "phi",
  MISTRAL = "mistral",
  GEMMA = "gemma",
  QWEN = "qwen",
  SMOL_LM = "smollm",
  WIZARD_MATH = "wizardmath",
  STABLE_LM = "stablelm",
  REDPAJAMA = "redpajama",
  DEEPSEEK = "DeepSeek",
}

// Catálogo del motor CPU (wllama/WASM) — respaldo cuando no hay WebGPU
// utilizable. Usa el mismo formato .gguf que el lado Python del proyecto.
//
// El modelo comprometido en la tesis (documentacion/decisiones/0001-alcance-
// y-hardware.md, Plan de Tesis/partes/05bFactibilidad.tex) es explícitamente
// Qwen2.5-3B-Instruct GGUF Q4_K_M como "modelo local por defecto", con 7B
// como "variante de calidad solo si hay RAM suficiente". 0.5B y 1.5B NO
// están en la tesis — se agregan solo como alternativas livianas para
// dispositivos que no puedan con el 3B por CPU pura.
//
// 7B NO entra a este catálogo (CPU/wllama): su .gguf pesa ~4.7 GB y supera
// el límite de 2 GB por archivo que documenta wllama (restricción del
// ArrayBuffer del navegador) — fallaría al cargar. El 7B como "variante de
// calidad" queda disponible del lado GPU (DEFAULT_MODEL_BASES / WebLLM),
// que sí soporta archivos grandes.
export interface WllamaModelSource {
  repo: string;
  file: string;
}

export const WLLAMA_MODEL_SOURCES: Record<string, WllamaModelSource> = {
  "Qwen2.5-0.5B-Instruct-Q4_K_M-GGUF": {
    repo: "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
    file: "qwen2.5-0.5b-instruct-q4_k_m.gguf",
  },
  "Qwen2.5-1.5B-Instruct-Q4_K_M-GGUF": {
    repo: "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
    file: "qwen2.5-1.5b-instruct-q4_k_m.gguf",
  },
  "Qwen2.5-3B-Instruct-Q4_K_M-GGUF": {
    repo: "Qwen/Qwen2.5-3B-Instruct-GGUF",
    file: "qwen2.5-3b-instruct-q4_k_m.gguf",
  },
};

export const DEFAULT_WLLAMA_MODELS: ModelRecord[] = [
  {
    // Primero en la lista a propósito: setModels() usa el primer modelo
    // como respaldo cuando el modelo previamente seleccionado no está en
    // el catálogo (ej. al pasar de GPU a CPU tras un error de hardware).
    // Ese cambio automático ocurre justo en los dispositivos más débiles
    // (los que no pudieron ni con la GPU), así que el respaldo tiene que
    // ser el modelo MÁS LIVIANO, no el de la tesis: el .gguf del 3B pesa
    // ~2 GB, y cargarlo (no solo descargarlo, sino además volcarlo a la
    // memoria del WASM de un solo hilo) puede tardar varios minutos o
    // directamente agotar la memoria disponible en un navegador móvil,
    // sin ningún error visible (se queda "colgado" en 100%). El 3B sigue
    // disponible para quien lo elija a mano desde el selector.
    name: "Qwen2.5-1.5B-Instruct-Q4_K_M-GGUF",
    display_name: "Qwen (CPU) — liviano",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    size: "1.5B",
    quantization: "Q4_K_M",
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-0.5B-Instruct-Q4_K_M-GGUF",
    display_name: "Qwen (CPU) — liviano",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    size: "0.5B",
    quantization: "Q4_K_M",
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-3B-Instruct-Q4_K_M-GGUF",
    display_name: "Qwen (CPU) — modelo de la tesis",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    size: "3B",
    quantization: "Q4_K_M",
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
];

// Catálogo recortado al plan de tesis: familia Qwen2.5-Instruct (candidato
// definido en 00_COMO_EMPEZAR.md) en varios tamaños para adaptarse al
// dispositivo del usuario, con las dos cuantizaciones más usadas de WebLLM
// (q4f16_1 para GPUs con soporte de shaders fp16, q4f32_1 como alternativa
// más compatible). Se retiraron las demás familias (Phi, Llama, Gemma,
// Mistral, DeepSeek, SmolLM, etc.) del web-llm-chat original por no ser
// parte del plan de tesis.
const DEFAULT_MODEL_BASES: ModelRecord[] = [
  {
    name: "Qwen2.5-0.5B-Instruct-q4f16_1-MLC",
    display_name: "Qwen",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-0.5B-Instruct-q4f32_1-MLC",
    display_name: "Qwen",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-1.5B-Instruct-q4f16_1-MLC",
    display_name: "Qwen",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-1.5B-Instruct-q4f32_1-MLC",
    display_name: "Qwen",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-3B-Instruct-q4f16_1-MLC",
    display_name: "Qwen — modelo de la tesis",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-3B-Instruct-q4f32_1-MLC",
    display_name: "Qwen — modelo de la tesis",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-7B-Instruct-q4f16_1-MLC",
    display_name: "Qwen — variante de calidad",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
  {
    name: "Qwen2.5-7B-Instruct-q4f32_1-MLC",
    display_name: "Qwen — variante de calidad",
    provider: "Alibaba",
    family: ModelFamily.QWEN,
    recommended_config: {
      temperature: 0.7,
      presence_penalty: 0,
      frequency_penalty: 0,
      top_p: 0.8,
    },
  },
];

export const DEFAULT_MODELS: ModelRecord[] = DEFAULT_MODEL_BASES.filter(
  (model) => {
    if (
      !prebuiltAppConfig.model_list.map((m) => m.model_id).includes(model.name)
    ) {
      console.warn(
        `Model ${model.name} not supported by current WebLLM version.`,
      );
      return false;
    }
    return true;
  },
).map((model) => ({
  ...model,
  size: getSize(model.name),
  quantization: getQuantization(model.name),
}));

export const CHAT_PAGE_SIZE = 15;
export const MAX_RENDER_MSG_COUNT = 45;

export const LOG_LEVELS = {
  TRACE: 0,
  DEBUG: 1,
  INFO: 2,
  WARN: 3,
  ERROR: 4,
  SILENT: 5,
};
