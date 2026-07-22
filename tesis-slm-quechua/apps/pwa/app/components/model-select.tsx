import React, { useState, useEffect, useCallback, useRef } from "react";
import { Cpu, Search } from "lucide-react";
import ModelRow from "./model-row";
import { modelDetailsList } from "../utils/model";

import style from "./model-select.module.scss";
import { Modal } from "./ui-lib";

import Locale from "../locales";
import { ModelFamily } from "../constant";
import { Model, useAppConfig } from "../store";

export interface ModelSearchProps {
  onClose: () => void;
  availableModels: string[];
  onSelectModel: (model: string) => void;
}

interface SearchInputProps {
  searchTerm: string;
  setSearchTerm: (term: string) => void;
  inputRef: React.RefObject<HTMLInputElement>;
}

const SearchInput: React.FC<SearchInputProps> = ({
  searchTerm,
  setSearchTerm,
  inputRef,
}) => {
  return (
    <div className={style["input-container"]}>
      <input
        ref={inputRef}
        type="text"
        placeholder={Locale.ModelSelect.SearchPlaceholder}
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className={style["input"]}
      />
      <Search className={style["input-icon"]} />
    </div>
  );
};

const ModelSelect: React.FC<ModelSearchProps> = ({
  onClose,
  availableModels,
  onSelectModel,
}) => {
  const config = useAppConfig();
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredModels, setFilteredModels] = useState<[string, string[]][]>(
    [],
  );
  const [expandedModels, setExpandedModels] = useState<Set<string>>(new Set());

  const determineModelIcon = (model: Model) => {
    const modelFamily = identifyModelFamily(model);
    const modelDetail = modelDetailsList.find(
      (md) => modelFamily && modelFamily === md.family,
    );
    return (
      <div className={style["model-icon"]}>
        {modelDetail?.icon ? <modelDetail.icon /> : <Cpu />}
      </div>
    );
  };

  const identifyModelFamily = (model: Model): ModelFamily | null => {
    return config.models.find((m) => m.name === model)?.family || null;
  };

  const extractModelDetails = (model: string) => {
    const parts = model.split("-");
    const displayName: string[] = [];
    const quantBadges: string[] = [];
    let isBadge = false;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (isBadge || part.startsWith("q") || part.startsWith("b")) {
        isBadge = true;
        if (part !== "MLC") {
          quantBadges.push(part);
        }
      } else {
        displayName.push(part);
      }
    }

    return {
      displayName: displayName.join(" "),
      quantBadge: quantBadges.length > 0 ? quantBadges.join("-") : null,
    };
  };

  const sortAndGroupModels = useCallback(
    (models: string[]): [string, string[]][] => {
      const groupedModels: { [key: string]: string[] } = {};

      for (const model of models) {
        const { displayName } = extractModelDetails(model);
        const family = identifyModelFamily(model);

        if (family) {
          if (!groupedModels[displayName]) {
            groupedModels[displayName] = [];
          }
          groupedModels[displayName].push(model);
        }
      }

      for (const key in groupedModels) {
        groupedModels[key].sort((a, b) => a.localeCompare(b));
      }

      return Object.entries(groupedModels).sort(
        ([, aVariants], [, bVariants]) => {
          const familyA = identifyModelFamily(aVariants[0]) || "";
          const familyB = identifyModelFamily(bVariants[0]) || "";
          return familyA.localeCompare(familyB);
        },
      );
    },
    [],
  );

  const handleToggleExpand = (modelName: string) => {
    setExpandedModels((prev) => {
      const updatedSet = new Set<string>(prev);
      if (updatedSet.has(modelName)) {
        updatedSet.delete(modelName);
      } else {
        updatedSet.add(modelName);
      }
      return updatedSet;
    });
  };

  useEffect(() => {
    const sortedModels = sortAndGroupModels(availableModels);

    let filtered = sortedModels;

    if (searchTerm) {
      const lowerSearchTerm = searchTerm.toLowerCase();
      filtered = sortedModels.filter(
        ([baseModel, variants]) =>
          baseModel.toLowerCase().includes(lowerSearchTerm) ||
          variants.some((v) => v.toLowerCase().includes(lowerSearchTerm)),
      );
    }

    setFilteredModels(filtered);
  }, [searchTerm, availableModels, sortAndGroupModels]);

  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setTimeout(() => {
      searchInputRef.current?.focus();
    }, 0);
  }, []);

  return (
    <div className="screen-model-container">
      <Modal title={Locale.ModelSelect.Title} onClose={onClose}>
        <div className={style["header"]}>
          <SearchInput
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            inputRef={searchInputRef}
          />
        </div>
        <div className={style["model-list"]}>
          {filteredModels.map((model) => (
            <ModelRow
              key={model[0]}
              baseModel={model[0]}
              variants={model[1]}
              isExpanded={expandedModels.has(model[0])}
              determineModelIcon={determineModelIcon}
              extractModelDetails={extractModelDetails}
              onSelectModel={onSelectModel}
              onClose={onClose}
              handleToggleExpand={handleToggleExpand}
            />
          ))}
        </div>
      </Modal>
    </div>
  );
};

export default ModelSelect;
