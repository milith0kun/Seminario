import React from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

import style from "./model-row.module.scss";
import { getRequisitosModelo } from "../utils/model";

interface ModelRowProps {
  baseModel: string;
  variants: string[];
  isExpanded: boolean;
  determineModelIcon: (model: string) => JSX.Element;
  extractModelDetails: (model: string) => {
    displayName: string;
    quantBadge: string | null;
  };
  onSelectModel: (model: string) => void;
  onClose: () => void;
  handleToggleExpand: (modelName: string) => void;
}

const ModelRow: React.FC<ModelRowProps> = ({
  baseModel,
  variants,
  isExpanded,
  determineModelIcon,
  extractModelDetails,
  onSelectModel,
  onClose,
  handleToggleExpand,
}) => {
  return (
    <div className={style["row"]} key={baseModel}>
      <div
        className={style["summary-continer"]}
        onClick={() => {
          handleToggleExpand(baseModel);
        }}
      >
        <div className={style["summary"]}>
          <div className={style["summary-model-info"]}>
            {determineModelIcon(variants[0])}
            <span>{baseModel}</span>
          </div>
          {isExpanded ? <ChevronUp /> : <ChevronDown />}
        </div>
      </div>
      {isExpanded && (
        <div className={style["expanded"]}>
          {variants.map((variant) => {
            const { quantBadge } = extractModelDetails(variant);
            const requisitos = getRequisitosModelo(variant);
            return (
              <div
                key={variant}
                onClick={() => {
                  onSelectModel(variant);
                  onClose();
                }}
                className={style["variant-option"]}
              >
                <span className={style["variant-label"]}>
                  {quantBadge || variant}
                </span>
                {requisitos && (
                  <span className={style["variant-requisitos"]}>
                    ~{requisitos.vramGB} GB VRAM mínima
                    {requisitos.gamaBaja ? " · gama baja OK" : ""}
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default ModelRow;
