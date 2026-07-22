import { useEffect, useState } from "react";
import { showToast } from "./components/ui-lib";
import Locale from "./locales";
import { RequestMessage } from "./client/api";
import { Model } from "./store";
import { ModelType, prebuiltAppConfig } from "@mlc-ai/web-llm";
import { ChatImage } from "./typing";

export function trimTopic(topic: string) {
  // Fix an issue where double quotes still show in the Indonesian language
  // This will remove the specified punctuation from the end of the string
  // and also trim quotes from both the start and end if they exist.
  console.log("TrimTopic", topic);
  return (
    topic
      // fix for gemini
      .replace(/^["""*]+|["""*]+$/g, "")
      .replace(/[，。！？"""、,.!?*]*$/, "")
      // remove think tags and content between them, including across multiple lines
      .replace(/<think>[\s\S]*?<\/think>/g, "")
  );
}

export async function copyToClipboard(text: string) {
  try {
    await navigator.clipboard.writeText(text);
    showToast(Locale.Copy.Success);
  } catch (error) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
      document.execCommand("copy");
      showToast(Locale.Copy.Success);
    } catch (error) {
      showToast(Locale.Copy.Failed);
    }
    document.body.removeChild(textArea);
  }
}

export async function downloadAs(text: string, filename: string) {
  const element = document.createElement("a");
  element.setAttribute(
    "href",
    "data:text/plain;charset=utf-8," + encodeURIComponent(text),
  );
  element.setAttribute("download", filename);

  element.style.display = "none";
  document.body.appendChild(element);

  element.click();

  document.body.removeChild(element);
}

export function compressImage(file: File, maxSize: number): Promise<ChatImage> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (readerEvent: any) => {
      const image = new Image();
      image.onload = () => {
        let canvas = document.createElement("canvas");
        let ctx = canvas.getContext("2d");
        let width = image.width;
        let height = image.height;
        let quality = 0.9;
        let dataUrl;

        do {
          canvas.width = width;
          canvas.height = height;
          ctx?.clearRect(0, 0, canvas.width, canvas.height);
          ctx?.drawImage(image, 0, 0, width, height);
          dataUrl = canvas.toDataURL("image/jpeg", quality);

          if (dataUrl.length < maxSize) break;

          if (quality > 0.5) {
            // Prioritize quality reduction
            quality -= 0.1;
          } else {
            // Then reduce the size
            width *= 0.9;
            height *= 0.9;
          }
        } while (dataUrl.length > maxSize);

        resolve({
          url: dataUrl,
          width: width,
          height: height,
        });
      };
      image.onerror = reject;
      image.src = readerEvent.target.result;
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

export function readFromFile() {
  return new Promise<string>((res, rej) => {
    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "application/json";

    fileInput.onchange = (event: any) => {
      const file = event.target.files[0];
      const fileReader = new FileReader();
      fileReader.onload = (e: any) => {
        res(e.target.result);
      };
      fileReader.onerror = (e) => rej(e);
      fileReader.readAsText(file);
    };

    fileInput.click();
  });
}

export function isIOS() {
  const userAgent = navigator.userAgent.toLowerCase();
  return /iphone|ipad|ipod/.test(userAgent);
}

export function useWindowSize() {
  const [size, setSize] = useState({
    width: window.innerWidth,
    height: window.innerHeight,
  });

  useEffect(() => {
    const onResize = () => {
      setSize({
        width: window.innerWidth,
        height: window.innerHeight,
      });
    };

    window.addEventListener("resize", onResize);

    return () => {
      window.removeEventListener("resize", onResize);
    };
  }, []);

  return size;
}

export const MOBILE_MAX_WIDTH = 600;
export function useMobileScreen() {
  const { width } = useWindowSize();

  return width <= MOBILE_MAX_WIDTH;
}

export function isFirefox() {
  return (
    typeof navigator !== "undefined" && /firefox/i.test(navigator.userAgent)
  );
}

export function selectOrCopy(el: HTMLElement, content: string) {
  const currentSelection = window.getSelection();

  if (currentSelection?.type === "Range") {
    return false;
  }

  copyToClipboard(content);

  return true;
}

function getDomContentWidth(dom: HTMLElement) {
  const style = window.getComputedStyle(dom);
  const paddingWidth =
    parseFloat(style.paddingLeft) + parseFloat(style.paddingRight);
  const width = dom.clientWidth - paddingWidth;
  return width;
}

function getOrCreateMeasureDom(id: string, init?: (dom: HTMLElement) => void) {
  let dom = document.getElementById(id);

  if (!dom) {
    dom = document.createElement("span");
    dom.style.position = "absolute";
    dom.style.wordBreak = "break-word";
    dom.style.fontSize = "14px";
    dom.style.transform = "translateY(-200vh)";
    dom.style.pointerEvents = "none";
    dom.style.opacity = "0";
    dom.id = id;
    document.body.appendChild(dom);
    init?.(dom);
  }

  return dom!;
}

export function autoGrowTextArea(dom: HTMLTextAreaElement) {
  const measureDom = getOrCreateMeasureDom("__measure");
  const singleLineDom = getOrCreateMeasureDom("__single_measure", (dom) => {
    dom.innerText = "TEXT_FOR_MEASURE";
  });

  const width = getDomContentWidth(dom);
  measureDom.style.width = width + "px";
  measureDom.innerText = dom.value !== "" ? dom.value : "1";
  measureDom.style.fontSize = dom.style.fontSize;
  const endWithEmptyLine = dom.value.endsWith("\n");
  const height = parseFloat(window.getComputedStyle(measureDom).height);
  const singleLineHeight = parseFloat(
    window.getComputedStyle(singleLineDom).height,
  );

  const rows =
    Math.round(height / singleLineHeight) + (endWithEmptyLine ? 1 : 0);

  return rows;
}

export function getCSSVar(varName: string) {
  return getComputedStyle(document.body).getPropertyValue(varName).trim();
}

/**
 * Detects Macintosh
 */
export function isMacOS(): boolean {
  if (typeof window !== "undefined") {
    let userAgent = window.navigator.userAgent.toLocaleLowerCase();
    const macintosh = /iphone|ipad|ipod|macintosh/.test(userAgent);
    return !!macintosh;
  }
  return false;
}

export function getMessageTextContent(message: RequestMessage) {
  if (typeof message.content === "string") {
    return message.content;
  }
  for (const c of message.content) {
    if (c.type === "text") {
      return c.text ?? "";
    }
  }
  return "";
}

export function getMessageImages(message: RequestMessage): ChatImage[] {
  if (typeof message.content === "string") {
    return [];
  }
  const urls: ChatImage[] = [];
  for (const c of message.content) {
    if (c.type === "image_url") {
      urls.push({
        url: c.image_url?.url ?? "",
        width: c.dimension?.width ?? 0,
        height: c.dimension?.height ?? 0,
      });
    }
  }
  return urls;
}

export const isVisionModel = (model: Model) =>
  prebuiltAppConfig.model_list.find((m) => m.model_id === model)?.model_type ===
  ModelType.VLM;

// Fix various problems in webllm generation
export function fixMessage(message: string) {
  // RedPajama model incorrectly includes `<human` in response
  message = message.replace(/(<human\s*)+$/, "");

  return message;
}

// Extrae un mensaje legible de cualquier tipo de error que puedan lanzar
// los motores (Error normal, DOM Event —ej. GPUUncapturedErrorEvent, que
// con err.toString() da literalmente "[object Event]"—, string, u otra
// cosa). Reemplaza el patrón repetido `err.message || err.toString()`.
export function extraerMensajeError(err: any): string {
  if (!err) return "";
  if (typeof err === "string") return err;
  if (err.message && typeof err.message === "string") return err.message;
  // DOM Event (ej. errores de WebGPU capturados como evento, o el
  // onerror de un Worker, en vez de un Error normal): buscar en
  // .error/.reason primero; si no hay, juntar todo lo que el Event traiga
  // (filename/lineno/colno/target) para no perder la única pista
  // disponible en vez de caer directo al genérico "[object Event]".
  if (typeof Event !== "undefined" && err instanceof Event) {
    const anidado = (err as any).error || (err as any).reason;
    if (anidado) return extraerMensajeError(anidado);

    const partes: string[] = [`tipo=${(err as any).type || "desconocido"}`];
    if ((err as any).filename) {
      partes.push(
        `archivo=${(err as any).filename}:${(err as any).lineno ?? "?"}:${(err as any).colno ?? "?"}`,
      );
    }
    const target = (err as any).target;
    if (target) {
      const desc =
        target.src || target.href || target.currentSrc || target.tagName;
      if (desc) partes.push(`origen=${desc}`);
    }
    return `Evento de error del navegador (${partes.join(", ")})`;
  }
  const texto = err.toString?.();
  if (texto && texto !== "[object Object]" && texto !== "[object Event]") {
    return texto;
  }
  try {
    return JSON.stringify(err);
  } catch {
    return "Error desconocido";
  }
}

// Traduce errores técnicos comunes del motor WebGPU/WebLLM a un mensaje
// entendible con pasos de recuperación, en vez de mostrar la traza cruda
// en la burbuja del chat.
export function traducirErrorModelo(
  errorMessage: string,
  modeloActual?: string,
  seEscaloACpu?: boolean,
): string {
  const msg = errorMessage || "";

  if (seEscaloACpu) {
    return (
      "⚠️ Este dispositivo no tiene WebGPU utilizable (se probó tanto el " +
      "motor normal como un motor alternativo, y ambos fallaron igual). " +
      "La app ya cambió, en esta misma conversación, a un **motor por " +
      "CPU** que no depende de GPU en absoluto — más lento, pero " +
      "funciona en cualquier celular o PC.\n\n" +
      "👉 Volvé a escribir tu mensaje: esta vez va a descargar un modelo " +
      "más chico optimizado para CPU y responder con eso, sin necesidad " +
      "de recargar la página.\n\n" +
      `Detalle técnico: ${msg.split("\n")[0]}`
    );
  }

  if (/Cache\.add\(\)|Cache\.put\(\)|NetworkError.*[Cc]ache/i.test(msg)) {
    return (
      "⚠️ Se cortó la descarga del modelo (problema de red momentáneo). " +
      "No perdiste la conversación. Espera a que se estabilice la " +
      "conexión y vuelve a mandar el mensaje para reintentar la " +
      "descarga.\n\n" +
      `Detalle técnico: ${msg.split("\n")[0]}`
    );
  }

  if (/ShaderModule|GPUPipelineError|reshape.*_kernel/i.test(msg)) {
    const esVarianteF16 = /f16/i.test(modeloActual || "");
    const modeloF32Sugerido = esVarianteF16
      ? modeloActual!.replace(/f16/i, "f32")
      : null;

    if (modeloF32Sugerido) {
      return (
        "⚠️ Tu navegador/GPU no soporta la extensión WebGPU \"shader-f16\" " +
        `que necesita "${modeloActual}". Esto no depende del tamaño del ` +
        "modelo (pasa igual con modelos chicos o grandes en f16) — hace " +
        "falta usar la variante f32, que no requiere esa extensión.\n\n" +
        `👉 Abre el selector de modelo y elige "${modeloF32Sugerido}" ` +
        "(mismo tamaño, sin el requisito f16).\n\n" +
        `Detalle técnico: ${msg.split("\n")[0]}`
      );
    }

    return (
      "⚠️ El navegador tuvo un problema al preparar el modelo en la GPU " +
      "(caché del modelo dañada, normalmente por una descarga que se " +
      "cortó a mitad). Esto no borra tu conversación. La app ya borró la " +
      "caché de este modelo y se preparó para usar un motor que se " +
      "reinicia limpio en cada recarga:\n" +
      "1. Recarga la página ahora (F5) y vuelve a mandar el mensaje — se " +
      "va a descargar el modelo de nuevo desde cero.\n" +
      "2. Si vuelve a fallar: actualiza los drivers de la GPU/el " +
      "navegador.\n\n" +
      `Detalle técnico: ${msg.split("\n")[0]}`
    );
  }

  if (/WebGPU/i.test(msg) && /not (available|supported)|compatibility/i.test(msg)) {
    return (
      "⚠️ Este navegador o dispositivo no tiene WebGPU disponible, y es " +
      "necesario para correr el modelo localmente. Prueba con Chrome o " +
      "Edge actualizados.\n\n" +
      `Detalle técnico: ${msg.split("\n")[0]}`
    );
  }

  if (/out of memory|oom/i.test(msg)) {
    return (
      "⚠️ El dispositivo no tiene memoria suficiente para este modelo. " +
      "Prueba con un tamaño más chico (0.5B o 1.5B) desde el selector de " +
      "modelo.\n\n" +
      `Detalle técnico: ${msg.split("\n")[0]}`
    );
  }

  return errorMessage;
}

// Get model size from model id
export function getSize(model_id: string): string | undefined {
  const sizeRegex = /-(\d+(\.\d+)?[BK])-?/;
  const match = model_id.match(sizeRegex);
  if (match) {
    return match[1];
  }
  return undefined;
}

// Get quantization method from model id
export function getQuantization(model_id: string): string | undefined {
  const quantizationRegex = /-(q[0-9]f[0-9]+(?:_[0-9])?)-/;
  const match = model_id.match(quantizationRegex);
  if (match) {
    return match[1];
  }
  return undefined;
}

export interface ModelLoadProgress {
  percent: number; // 0-100
  step: string; // ej. "Descargando modelo", "Cargando desde caché"
  detail: string; // ej. "(44/88)"
  secsElapsed?: number;
}

// WebLLM reporta el progreso de descarga/carga como texto plano (ver
// InitProgressReport en @mlc-ai/web-llm), con formatos estables tipo:
// "Fetching param cache[44/88]: 2059MB fetched. 50% completed, 182 secs elapsed."
// "Loading model from cache[3/88]: 12% completed, 4 secs elapsed."
// "Finish loading on WebGPU"
// Esto lo convierte en algo que se puede mostrar como barra de progreso
// en vez de texto crudo dentro de la burbuja de chat.
export function parseModelLoadProgress(text: string): ModelLoadProgress | null {
  if (/^finish loading/i.test(text)) {
    return { percent: 100, step: "Modelo listo", detail: "" };
  }

  const match = text.match(
    /^(Fetching param cache|Loading model from cache)\[(\d+)\/(\d+)\]:.*?(\d+)% completed, (\d+) secs elapsed/i,
  );
  if (match) {
    const [, stage, iter, total, percent, secs] = match;
    return {
      percent: Number(percent),
      step:
        stage.toLowerCase().startsWith("fetching")
          ? "Descargando modelo"
          : "Cargando modelo desde caché",
      detail: `(${iter}/${total})`,
      secsElapsed: Number(secs),
    };
  }

  const cpuMatch = text.match(
    /^Descargando modelo \(CPU\).*?(\d+)% completed, (\d+) secs elapsed/i,
  );
  if (cpuMatch) {
    return {
      percent: Number(cpuMatch[1]),
      step: "Descargando modelo (CPU)",
      detail: "",
      secsElapsed: Number(cpuMatch[2]),
    };
  }

  const genericMatch = text.match(/(\d+)% completed, (\d+) secs elapsed/i);
  if (genericMatch) {
    return {
      percent: Number(genericMatch[1]),
      step: "Preparando modelo",
      detail: "",
      secsElapsed: Number(genericMatch[2]),
    };
  }

  return null;
}
