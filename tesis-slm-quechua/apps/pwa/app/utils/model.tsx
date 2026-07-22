import React from "react";
import { prebuiltAppConfig } from "@mlc-ai/web-llm";
import { ModelRecord } from "../client/api";
import { ModelFamily } from "../constant";

export function collectModelTable(
  models: readonly ModelRecord[],
  customModels: string,
) {
  const modelTable: Record<
    string,
    {
      name: string;
      display_name: string;
      provider?: ModelRecord["provider"]; // Marked as optional
      isDefault?: boolean;
    }
  > = {};

  // default models
  models.forEach((m) => {
    modelTable[m.name] = {
      ...m,
      display_name: m.name, // 'provider' is copied over if it exists
    };
  });

  // server custom models
  customModels
    .split(",")
    .filter((v) => !!v && v.length > 0)
    .forEach((m) => {
      const available = !m.startsWith("-");
      const nameConfig =
        m.startsWith("+") || m.startsWith("-") ? m.slice(1) : m;
      const [name, display_name] = nameConfig.split("=");

      modelTable[name] = {
        name,
        display_name: display_name || name,
        provider: modelTable[name]?.provider ?? "", // Use optional chaining
      };
    });

  return modelTable;
}

/**
 * Generate full model table.
 */
export function collectModels(
  models: readonly ModelRecord[],
  customModels: string,
) {
  const modelTable = collectModelTable(models, customModels);
  const allModels = Object.values(modelTable);

  return allModels;
}

export interface ModelDetails {
  family: ModelFamily;
  name: string;
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
}

// Recortado al plan de tesis: solo Qwen (las demás familias del
// web-llm-chat original ya no están en el catálogo de modelos, ver
// DEFAULT_MODEL_BASES en constant.ts).
export const modelDetailsList: ModelDetails[] = [
  {
    family: ModelFamily.QWEN,
    name: "Qwen",
    icon: (...props) => <img src="./qwen.webp" alt="Qwen Logo" {...props} />,
  },
];

export interface RequisitosModelo {
  vramGB: number;
  gamaBaja: boolean; // low_resource_required: corre en GPUs modestas
}

// Datos oficiales de WebLLM (prebuiltAppConfig.model_list) sobre cuánta
// VRAM necesita cada variante para correr, para ayudar a elegir según el
// dispositivo. No es el tamaño de descarga exacto, pero es la referencia
// más confiable de "capacidad mínima" que expone la librería.
export function getRequisitosModelo(modelId: string): RequisitosModelo | undefined {
  const record = prebuiltAppConfig.model_list.find(
    (m) => m.model_id === modelId,
  );
  if (!record || typeof record.vram_required_MB !== "number") {
    return undefined;
  }
  return {
    vramGB: Math.round((record.vram_required_MB / 1024) * 10) / 10,
    gamaBaja: record.low_resource_required ?? false,
  };
}
