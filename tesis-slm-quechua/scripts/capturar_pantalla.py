import subprocess
import os

ADB = r"C:\Users\PC\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEST = r"C:\Users\PC\.gemini\antigravity-ide\brain\d573b5e7-1a0f-4cc7-9f7f-f97054a12636\captura_chat_final.png"

subprocess.run([ADB, "shell", "screencap", "-p", "/sdcard/captura_chat_final.png"], check=True)
subprocess.run([ADB, "pull", "/sdcard/captura_chat_final.png", DEST], check=True)

if os.path.exists(DEST):
    print(f"Screenshot guardado exitosamente: {os.path.getsize(DEST)} bytes")
else:
    print("Error al guardar screenshot")
