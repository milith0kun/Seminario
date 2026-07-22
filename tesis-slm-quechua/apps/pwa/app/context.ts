import { createContext } from "react";
import { WebLLMApi } from "./client/webllm";
import { ModelRecord } from "./client/api";
import { MlcLLMApi } from "./client/mlcllm";
import { WllamaApi } from "./client/wllama";

export const WebLLMContext = createContext<WebLLMApi | undefined>(undefined);
export const MLCLLMContext = createContext<MlcLLMApi | undefined>(undefined);
export const WllamaContext = createContext<WllamaApi | undefined>(undefined);
