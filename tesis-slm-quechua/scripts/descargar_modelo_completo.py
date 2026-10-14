import os
import sys
import urllib.request

URL = "https://huggingface.co/litert-community/Qwen2.5-Coder-3B-Instruct/resolve/main/Qwen2.5_Coder_3B_It.litertlm?download=true"
DEST_DIR = r"D:\Proyectos\Seminario\tesis-slm-quechua\models"
DEST_FILE = os.path.join(DEST_DIR, "Qwen2.5_Coder_3B_It.litertlm")

os.makedirs(DEST_DIR, exist_ok=True)

def reporthook(blocknum, blocksize, totalsize):
    readsofar = blocknum * blocksize
    if totalsize > 0:
        percent = readsofar * 1e2 / totalsize
        s = f"\rDescargando: {percent:5.1f}% ({readsofar / (1024*1024):.1f} MB / {totalsize / (1024*1024):.1f} MB)"
        sys.stderr.write(s)
        if readsofar >= totalsize:
            sys.stderr.write("\n")
    else:
        sys.stderr.write(f"\rDescargados: {readsofar / (1024*1024):.1f} MB")

print(f"Descargando archivo completo a {DEST_FILE}...")
urllib.request.urlretrieve(URL, DEST_FILE, reporthook)
print("\n¡Descarga completa con éxito!")
