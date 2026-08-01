"use client";

require("../polyfill");

import styles from "./home.module.scss";

import log from "loglevel";
import dynamic from "next/dynamic";
import { useState, useEffect, useRef } from "react";
import {
  HashRouter as Router,
  Routes,
  Route,
  useLocation,
} from "react-router-dom";
import { ServiceWorkerMLCEngine } from "@mlc-ai/web-llm";

import MlcIcon from "../icons/mlc.svg";
import LoadingIcon from "../icons/three-dots.svg";

import Locale from "../locales";
import { getCSSVar, useMobileScreen } from "../utils";
import {
  DEFAULT_MODELS,
  DEFAULT_WLLAMA_MODELS,
  Path,
  SlotID,
  FORZAR_WEBWORKER_KEY,
  FORZAR_CPU_KEY,
} from "../constant";
import { ErrorBoundary } from "./error";
import { getISOLang, getLang } from "../locales";
import { SideBar } from "./sidebar";
import { useAppConfig, DEFAULT_MODEL, Model, CacheType } from "../store/config";
import { WebLLMApi } from "../client/webllm";
import { ModelClient, useChatStore } from "../store";
import { MLCLLMContext, WebLLMContext, WllamaContext } from "../context";
import { MlcLLMApi } from "../client/mlcllm";
import { WllamaApi } from "../client/wllama";
import { showToast } from "./ui-lib";

export function Loading(props: { noLogo?: boolean }) {
  return (
    <div className={styles["loading-content"] + " no-dark"}>
      {!props.noLogo && (
        <div className={styles["loading-content-logo"] + " no-dark mlc-icon"}>
          <MlcIcon />
        </div>
      )}
      <LoadingIcon />
    </div>
  );
}

export function ErrorScreen(props: { message: string }) {
  return (
    <div className={styles["error-screen"] + " no-dark"}>
      <p>{props.message}</p>
    </div>
  );
}

const Settings = dynamic(async () => (await import("./settings")).Settings, {
  loading: () => <Loading noLogo />,
});

const Chat = dynamic(async () => (await import("./chat")).Chat, {
  loading: () => <Loading noLogo />,
});

const TemplatePage = dynamic(
  async () => (await import("./template")).TemplatePage,
  {
    loading: () => <Loading noLogo />,
  },
);

export function useSwitchTheme() {
  const config = useAppConfig();

  useEffect(() => {
    document.body.classList.remove("light");
    document.body.classList.remove("dark");

    if (config.theme === "dark") {
      document.body.classList.add("dark");
    } else if (config.theme === "light") {
      document.body.classList.add("light");
    }

    const metaDescriptionDark = document.querySelector(
      'meta[name="theme-color"][media*="dark"]',
    );
    const metaDescriptionLight = document.querySelector(
      'meta[name="theme-color"][media*="light"]',
    );

    if (config.theme === "auto") {
      metaDescriptionDark?.setAttribute("content", "#151515");
      metaDescriptionLight?.setAttribute("content", "#fafafa");
    } else {
      const themeColor = getCSSVar("--theme-color");
      metaDescriptionDark?.setAttribute("content", themeColor);
      metaDescriptionLight?.setAttribute("content", themeColor);
    }
  }, [config.theme]);
}

function useHtmlLang() {
  useEffect(() => {
    const lang = getISOLang();
    const htmlLang = document.documentElement.lang;

    if (lang !== htmlLang) {
      document.documentElement.lang = lang;
    }
  }, []);
}

const useHasHydrated = () => {
  const [hasHydrated, setHasHydrated] = useState<boolean>(false);

  useEffect(() => {
    setHasHydrated(true);
  }, []);

  return hasHydrated;
};

const loadAsyncFonts = () => {
  const linkEl = document.createElement("link");
  linkEl.rel = "stylesheet";
  linkEl.href = "/fonts/font.css";
  document.head.appendChild(linkEl);
};

function Screen() {
  const config = useAppConfig();
  const location = useLocation();
  const isHome = location.pathname === Path.Home;
  const isMobileScreen = useMobileScreen();
  const shouldTightBorder = config.tightBorder && !isMobileScreen;

  useEffect(() => {
    loadAsyncFonts();
  }, []);

  return (
    <div
      className={
        styles.container +
        ` ${shouldTightBorder ? styles["tight-container"] : styles.container} ${
          getLang() === "ar" ? styles["rtl-screen"] : ""
        }`
      }
    >
      <>
        <SideBar className={isHome ? styles["sidebar-show"] : ""} />

        <div className={styles["window-content"]} id={SlotID.AppBody}>
          <Routes>
            <Route path={Path.Home} element={<Chat />} />
            <Route path={Path.Templates} element={<TemplatePage />} />
            <Route path={Path.Chat} element={<Chat />} />
            <Route path={Path.Settings} element={<Settings />} />
          </Routes>
        </div>
      </>
    </div>
  );
}

const useWebLLM = () => {
  const config = useAppConfig();
  const [webllm, setWebLLM] = useState<WebLLMApi | undefined>(undefined);
  const [isWebllmActive, setWebllmAlive] = useState(false);

  const isWebllmInitialized = useRef(false);
  const useIndexedDBCache = config.cacheType === CacheType.IndexDB;

  // If service worker registration timeout, fall back to web worker
  const timeout = setTimeout(() => {
    if (!isWebllmInitialized.current && !isWebllmActive && !webllm) {
      log.info(
        "Service Worker activation is timed out. Falling back to use web worker.",
      );
      setWebLLM(new WebLLMApi("webWorker", config.logLevel, useIndexedDBCache));
      setWebllmAlive(true);
    }
  }, 2_000);

  // Initialize WebLLM engine
  useEffect(() => {
    if (
      typeof window !== "undefined" &&
      window.localStorage.getItem(FORZAR_WEBWORKER_KEY) === "1"
    ) {
      log.info(
        "Se fuerza WebWorkerMLCEngine (recuperación tras error de GPU previo).",
      );
      setWebLLM(new WebLLMApi("webWorker", config.logLevel, useIndexedDBCache));
      setWebllmAlive(true);
      isWebllmInitialized.current = true;
      clearTimeout(timeout);
      return;
    }

    if ("serviceWorker" in navigator) {
      log.info("Service Worker API is available and in use.");
      navigator.serviceWorker.ready.then(() => {
        log.info("Service Worker is activated.");
        // Check whether WebGPU is available in Service Worker
        const request = {
          kind: "checkWebGPUAvilability",
          uuid: crypto.randomUUID(),
          content: "",
        };

        const sendEventInterval = setInterval(() => {
          navigator.serviceWorker.controller?.postMessage(request);
        }, 200);

        const webGPUCheckCallback = (event: MessageEvent) => {
          const message = event.data;
          if (message.kind === "return" && message.uuid === request.uuid) {
            const isWebGPUAvailable = message.content;
            log.info(
              isWebGPUAvailable
                ? "Service Worker has WebGPU Available."
                : "Service Worker does not have available WebGPU.",
            );
            if (!webllm && !isWebllmActive) {
              setWebLLM(
                new WebLLMApi(
                  isWebGPUAvailable ? "serviceWorker" : "webWorker",
                  config.logLevel,
                  useIndexedDBCache,
                ),
              );
              setWebllmAlive(true);
              isWebllmInitialized.current = true;
              clearTimeout(timeout);
            }
            navigator.serviceWorker.removeEventListener(
              "message",
              webGPUCheckCallback,
            );
            clearInterval(sendEventInterval);
          }
        };
        navigator.serviceWorker.addEventListener(
          "message",
          webGPUCheckCallback,
        );
      });
    } else {
      log.info(
        "Service Worker API is unavailable. Falling back to use web worker.",
      );
      setWebLLM(new WebLLMApi("webWorker", config.logLevel, useIndexedDBCache));
      setWebllmAlive(true);
      isWebllmInitialized.current = true;
      clearTimeout(timeout);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (webllm?.webllm.type === "serviceWorker") {
    setInterval(() => {
      if (webllm) {
        // 10s per heartbeat, dead after 30 seconds of inactivity
        setWebllmAlive(
          !!webllm.webllm.engine &&
            (webllm.webllm.engine as ServiceWorkerMLCEngine).missedHeartbeat < 3,
        );
      }
    }, 10_000);
  }
  return { webllm, isWebllmActive };
};

const useMlcLLM = () => {
  const config = useAppConfig();
  const [mlcllm, setMlcLlm] = useState<MlcLLMApi | undefined>(undefined);

  useEffect(() => {
    setMlcLlm(new MlcLLMApi(config.modelConfig.mlc_endpoint));
  }, [config.modelConfig.mlc_endpoint, setMlcLlm]);

  return mlcllm;
};

// Motor de respaldo 100% por CPU (wllama/WASM), para dispositivos sin
// WebGPU utilizable. Se crea una sola vez; a diferencia de useWebLLM(),
// nunca bloquea el gate de carga de Home().
const useWllama = () => {
  const config = useAppConfig();
  const [wllama, setWllama] = useState<WllamaApi | undefined>(undefined);

  useEffect(() => {
    setWllama(new WllamaApi(config.logLevel));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return wllama;
};

// Decide si este dispositivo debe usar el motor CPU desde el arranque:
// - No hay `navigator.gpu` en absoluto (WebGPU ni siquiera existe), o
// - Ya se marcó FORZAR_CPU_KEY tras fallar repetidamente con GPU
//   (ver degradación automática en store/chat.ts).
function debeUsarMotorCpu(): boolean {
  if (typeof window === "undefined" || typeof navigator === "undefined") {
    return false;
  }
  const hayWebGPU = "gpu" in navigator;
  const forzado = window.localStorage.getItem(FORZAR_CPU_KEY) === "1";
  return !hayWebGPU || forzado;
}

const useUsarMotorCpu = () => {
  const config = useAppConfig();
  const [usarCpu, setUsarCpu] = useState(false);

  useEffect(() => {
    const cpu = debeUsarMotorCpu();
    setUsarCpu(cpu);
    if (cpu && config.modelClientType !== ModelClient.WLLAMA_CPU) {
      config.update((c) => {
        c.modelClientType = ModelClient.WLLAMA_CPU;
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return usarCpu;
};

// Muchos navegadores/GPUs no soportan la extensión WebGPU "shader-f16"
// (confirmado en pruebas: falla igual en Service Worker y en WebWorker con
// GPUPipelineError/ShaderModule inválido, cualquiera sea el tamaño de
// modelo). Si el modelo guardado en este dispositivo (de una sesión
// anterior, quizás antes de este fix) es una variante "q4f16_1", se migra
// a su par "q4f32_1" ANTES de que se intente cargar — así se evita repetir
// dos intentos fallidos de GPU (con cientos de errores de shader en
// consola) solo para terminar cayendo al motor CPU innecesariamente,
// cuando el dispositivo sí puede usar GPU sin la extensión f16.
const useMigrarModeloSinF16 = (usarCpu: boolean) => {
  const config = useAppConfig();

  useEffect(() => {
    if (usarCpu) return;
    if (typeof navigator === "undefined" || !("gpu" in navigator)) return;
    if (!config.modelConfig.model.includes("q4f16_1")) return;

    let cancelado = false;
    navigator.gpu
      ?.requestAdapter()
      .then((adapter) => {
        if (cancelado || !adapter) return;
        if (adapter.features.has("shader-f16")) return;

        const modeloActual = config.modelConfig.model;
        const modeloF32 = modeloActual.replace("q4f16_1", "q4f32_1");
        const existeF32 = DEFAULT_MODELS.some((m) => m.name === modeloF32);
        const destino = existeF32 ? modeloF32 : DEFAULT_MODEL;

        log.info(
          `Este dispositivo no soporta la extensión WebGPU "shader-f16". ` +
            `Se migra el modelo de "${modeloActual}" a "${destino}".`,
        );
        showToast(
          `Este dispositivo no admite modelos "f16". Se cambió a "${destino}".`,
        );
        config.selectModel(destino as Model);
      })
      .catch(() => {
        // Si requestAdapter falla, se deja que el flujo normal de carga
        // reporte el error (no hay nada más que migrar aquí).
      });

    return () => {
      cancelado = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usarCpu]);
};

// Sin este permiso, el navegador considera la caché del modelo (Cache
// Storage / IndexedDB, cientos de MB a varios GB) como "best-effort" y
// puede liberarla sola bajo presión de espacio (frecuente en celulares),
// aunque el código nunca la borre — causa típica de "se descarga el
// modelo cada vez que abro la app" sin ningún error de por medio.
const useAlmacenamientoPersistente = () => {
  useEffect(() => {
    if (typeof navigator === "undefined" || !navigator.storage?.persist) {
      return;
    }
    navigator.storage
      .persisted()
      .then((yaPersistente) => {
        if (yaPersistente) return;
        return navigator.storage.persist();
      })
      .then((concedido) => {
        if (concedido === undefined) return;
        log.info(
          concedido
            ? "Almacenamiento persistente concedido: la caché del modelo no debería liberarse sola."
            : "Almacenamiento persistente NO concedido por el navegador: la caché del modelo podría liberarse bajo presión de espacio.",
        );
      })
      .catch((err) => log.warn("No se pudo solicitar almacenamiento persistente:", err));
  }, []);
};

const useLoadUrlParam = () => {
  const config = useAppConfig();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    let modelConfig: any = {
      model: params.get("model"),
      temperature: params.has("temperature")
        ? parseFloat(params.get("temperature")!)
        : null,
      top_p: params.has("top_p") ? parseFloat(params.get("top_p")!) : null,
      max_tokens: params.has("max_tokens")
        ? parseInt(params.get("max_tokens")!)
        : null,
      presence_penalty: params.has("presence_penalty")
        ? parseFloat(params.get("presence_penalty")!)
        : null,
      frequency_penalty: params.has("frequency_penalty")
        ? parseFloat(params.get("frequency_penalty")!)
        : null,
    };
    Object.keys(modelConfig).forEach((key) => {
      // If the value of the key is null, delete the key
      if (modelConfig[key] === null) {
        delete modelConfig[key];
      }
    });
    if (Object.keys(modelConfig).length > 0) {
      log.info("Loaded model config from URL params", modelConfig);
      config.updateModelConfig(modelConfig);
    }
  }, []);
};

const useStopStreamingMessages = () => {
  const chatStore = useChatStore();

  // Clean up bad chat messages due to refresh during generating
  useEffect(() => {
    chatStore.stopStreaming();
  }, []);
};

const useLogLevel = (webllm?: WebLLMApi) => {
  const config = useAppConfig();

  // Update log level once app config loads
  useEffect(() => {
    log.setLevel(config.logLevel);
    if (webllm?.webllm?.engine) {
      webllm.webllm.engine.setLogLevel(config.logLevel);
    }
  }, [config.logLevel, webllm?.webllm?.engine]);
};

const useModels = (mlcllm: MlcLLMApi | undefined) => {
  const config = useAppConfig();

  useEffect(() => {
    if (config.modelClientType == ModelClient.WEBLLM) {
      config.setModels(DEFAULT_MODELS);
    } else if (config.modelClientType == ModelClient.MLCLLM_API) {
      if (mlcllm) {
        mlcllm.models().then((models) => {
          config.setModels(models);
        });
      }
    } else if (config.modelClientType == ModelClient.WLLAMA_CPU) {
      config.setModels(DEFAULT_WLLAMA_MODELS);
    }
  }, [config.modelClientType, mlcllm]);
};

export function Home() {
  const hasHydrated = useHasHydrated();
  useAlmacenamientoPersistente();
  const usarCpu = useUsarMotorCpu();
  useMigrarModeloSinF16(usarCpu);
  const { webllm, isWebllmActive } = useWebLLM();
  const mlcllm = useMlcLLM();
  const wllama = useWllama();

  useSwitchTheme();
  useHtmlLang();
  useLoadUrlParam();
  useStopStreamingMessages();
  useModels(mlcllm);
  useLogLevel(webllm);

  if (!hasHydrated) {
    return <Loading />;
  }

  // En modo CPU (sin WebGPU utilizable) no se exige que el motor GPU
  // (webllm/isWebllmActive) esté listo — solo que el motor CPU exista.
  if (usarCpu) {
    if (!wllama) {
      return <Loading />;
    }
  } else if (!webllm || !isWebllmActive) {
    return <Loading />;
  }

  return (
    <ErrorBoundary>
      <Router>
        <WebLLMContext.Provider value={webllm}>
          <MLCLLMContext.Provider value={mlcllm}>
            <WllamaContext.Provider value={wllama}>
              <Screen />
            </WllamaContext.Provider>
          </MLCLLMContext.Provider>
        </WebLLMContext.Provider>
      </Router>
    </ErrorBoundary>
  );
}
