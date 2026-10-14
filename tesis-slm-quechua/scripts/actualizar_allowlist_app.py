import json

ALLOWLIST_PATH = r"D:\Proyectos\Seminario\repos-externos\gallery\model_allowlists\1_0_19.json"
ROOT_ALLOWLIST_PATH = r"D:\Proyectos\Seminario\repos-externos\gallery\model_allowlist.json"

with open(ALLOWLIST_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

# Catálogo oficial de la Tesis con minDeviceMemoryInGb=4 para compatibilidad total con emulador y dispositivos móviles de 4GB
thesis_models = [
    {
        "name": "Qwen2.5-3B Base (E1 Control - E2 con RAG)",
        "modelId": "litert-community/Qwen2.5-Coder-3B-Instruct",
        "modelFile": "Qwen2.5_Coder_3B_It.litertlm",
        "description": "Modelo base original (3B). Permite evaluar el Escenario E1 (Control Zero-Shot con RAG apagado) y el Escenario E2 (SLM + RAG Curricular MINEDU con RAG encendido).",
        "sizeInBytes": 3433083824,
        "minDeviceMemoryInGb": 4,
        "commitHash": "a32e9f082c3fee8adcbe71990eae1eaca3eb0eb9",
        "defaultConfig": {
            "topK": 40,
            "topP": 0.8,
            "temperature": 0.7,
            "maxTokens": 2048,
            "accelerators": "cpu,gpu"
        },
        "taskTypes": ["llm_chat", "llm_prompt_lab", "llm_agent_chat"],
        "bestForTaskTypes": ["llm_chat", "llm_prompt_lab"]
    },
    {
        "name": "Qwen2.5-3B Tutor EIB (E3 Entrenado)",
        "modelId": "litert-community/Qwen2.5-3B-Instruct-QLoRA-Quechua",
        "modelFile": "Qwen2.5_Coder_3B_It.litertlm",
        "description": "Modelo adaptado con matrices entrenadas para tutoría EIB. Especializado en andamiaje pedagógico bilingüe y resiliencia morfológica en Quechua Collao con RAG activo.",
        "sizeInBytes": 3433083824,
        "minDeviceMemoryInGb": 4,
        "commitHash": "a32e9f082c3fee8adcbe71990eae1eaca3eb0eb9",
        "defaultConfig": {
            "topK": 40,
            "topP": 0.8,
            "temperature": 0.7,
            "maxTokens": 2048,
            "accelerators": "cpu,gpu"
        },
        "taskTypes": ["llm_chat", "llm_prompt_lab", "llm_agent_chat"],
        "bestForTaskTypes": ["llm_chat", "llm_prompt_lab"]
    },
    {
        "name": "Qwen2.5-1.5B Base (Variante Ligera E1 - E2)",
        "modelId": "litert-community/Qwen2.5-1.5B-Instruct",
        "modelFile": "Qwen2.5-1.5B-Instruct_multi-prefill-seq_q8_ekv4096.litertlm",
        "description": "Variante base compacta de 1.5B para evaluación de eficiencia en smartphones y tablets de 4 GB RAM.",
        "sizeInBytes": 1597931520,
        "minDeviceMemoryInGb": 4,
        "commitHash": "19edb84c69a0212f29a6ef17ba0d6f278b6a1614",
        "defaultConfig": {
            "topK": 40,
            "topP": 0.8,
            "temperature": 0.7,
            "maxTokens": 2048,
            "accelerators": "cpu,gpu"
        },
        "taskTypes": ["llm_chat", "llm_prompt_lab", "llm_agent_chat"],
        "bestForTaskTypes": ["llm_chat", "llm_prompt_lab"]
    },
    {
        "name": "Llama-3.2-3B Base (Comparativa Meta)",
        "modelId": "litert-community/Llama-3.2-3B",
        "modelFile": "llama3_2_3b_mixed_int4_gpu.litertlm",
        "description": "Modelo base alternativo Llama 3.2 de 3B cuantizado en Int4 para el benchmark comparativo frente a Qwen 2.5.",
        "sizeInBytes": 2000000000,
        "minDeviceMemoryInGb": 4,
        "commitHash": "401735124eace78bbaee7bbf8f95581ab2ee63af",
        "defaultConfig": {
            "topK": 40,
            "topP": 0.9,
            "temperature": 0.8,
            "maxTokens": 2048,
            "accelerators": "cpu,gpu"
        },
        "taskTypes": ["llm_chat", "llm_prompt_lab", "llm_agent_chat"],
        "bestForTaskTypes": ["llm_chat", "llm_prompt_lab"]
    },
    {
        "name": "Gemma-2-2B-IT Base (Comparativa Google)",
        "modelId": "litert-community/Gemma2-2B-IT",
        "modelFile": "Gemma2-2B-IT_multi-prefill-seq_q8_ekv1280.task",
        "description": "Modelo base alternativo Gemma 2 de 2B para comparación de rendimiento en el benchmark.",
        "sizeInBytes": 1900000000,
        "minDeviceMemoryInGb": 4,
        "commitHash": "0f2722125e4cd85da620e6a0ebcb26b87a230049",
        "defaultConfig": {
            "topK": 64,
            "topP": 0.95,
            "temperature": 1.0,
            "maxTokens": 1024,
            "accelerators": "cpu,gpu"
        },
        "taskTypes": ["llm_chat", "llm_prompt_lab"],
        "bestForTaskTypes": ["llm_chat", "llm_prompt_lab"]
    }
]

# Filtrar modelos antiguos que coincidan con los IDs
thesis_ids = {m["modelId"] for m in thesis_models}
other_models = [m for m in data["models"] if m.get("modelId") not in thesis_ids]

# Colocar modelos de tesis al inicio
data["models"] = thesis_models + other_models

with open(ALLOWLIST_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

with open(ROOT_ALLOWLIST_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Actualizado correctamente con minDeviceMemoryInGb=4.")
