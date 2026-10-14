import json
import re

JSON_PATH = r"D:\Proyectos\Seminario\repos-externos\gallery\model_allowlists\1_0_19.json"
KT_PATH = r"D:\Proyectos\Seminario\repos-externos\gallery\Android\src\app\src\main\java\com\google\ai\edge\gallery\ui\modelmanager\ModelManagerViewModel.kt"

with open(JSON_PATH, "r", encoding="utf-8") as f:
    json_obj = json.load(f)

json_compact = json.dumps(json_obj, ensure_ascii=False)
escaped_json = json_compact.replace('\\', '\\\\').replace('"', '\\"').replace('$', '\\$')

with open(KT_PATH, "r", encoding="utf-8") as f:
    kt_content = f.read()

pattern = r'private const val TEST_MODEL_ALLOW_LIST = ".*"'
replacement = f'private const val TEST_MODEL_ALLOW_LIST = "{escaped_json}"'

new_kt_content, count = re.subn(pattern, replacement, kt_content)
if count > 0:
    with open(KT_PATH, "w", encoding="utf-8") as f:
        f.write(new_kt_content)
    print("TEST_MODEL_ALLOW_LIST reemplazado con éxito con escape de caracteres.")
else:
    print("No se encontró el patrón regex en ModelManagerViewModel.kt")
