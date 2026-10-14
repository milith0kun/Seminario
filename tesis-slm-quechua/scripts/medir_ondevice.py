"""Medicion de eficiencia on-device en el emulador/dispositivo Android.

Complementa el benchmark de escritorio: las cifras de `evaluar_escenarios.py`
provienen de llama.cpp sobre CPU x86 y no representan el runtime LiteRT que
ejecuta realmente la app. Este script mide sobre el dispositivo:

  - TTFT y throughput reportados por la propia app en el logcat
  - RAM del proceso (PSS / heap nativo) durante la inferencia
  - Huella en disco del binario y de la cache compilada XNNPack

Requiere que la app este instalada y el modelo ya transferido.

Uso:
    python scripts/medir_ondevice.py --dispositivo emulator-5554 \
        --escenario E1 --repeticiones 3
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAQUETE = "com.google.aiedge.gallery"
ACTIVIDAD = f"{PAQUETE}/com.google.ai.edge.gallery.MainActivity"
DIR_APP = f"/storage/emulated/0/Android/data/{PAQUETE}/files"

CONSULTAS = [
    "Que es la fotosintesis?",
    "Como se organiza el trabajo comunal en el ayllu?",
    "Imatan yachanki yakuq muyuyninmanta?",
]


def adb_path() -> str:
    local = os.environ.get("LOCALAPPDATA", "")
    candidato = Path(local) / "Android" / "Sdk" / "platform-tools" / "adb.exe"
    return str(candidato) if candidato.exists() else "adb"


class Dispositivo:
    def __init__(self, serie: str):
        self.adb = adb_path()
        self.serie = serie

    def shell(self, comando: str, timeout: int = 60) -> str:
        r = subprocess.run(
            [self.adb, "-s", self.serie, "shell", comando],
            capture_output=True, text=True, timeout=timeout, errors="replace",
        )
        return r.stdout

    def ejecutar(self, *args: str, timeout: int = 60) -> str:
        r = subprocess.run(
            [self.adb, "-s", self.serie, *args],
            capture_output=True, text=True, timeout=timeout, errors="replace",
        )
        return r.stdout

    # -- estado del dispositivo ---------------------------------------

    def info(self) -> dict:
        mem = self.shell("cat /proc/meminfo | head -3")
        total = re.search(r"MemTotal:\s+(\d+)", mem)
        disco = self.shell("df /data | tail -1").split()
        return {
            "serie": self.serie,
            "modelo": self.shell("getprop ro.product.model").strip(),
            "abi": self.shell("getprop ro.product.cpu.abi").strip(),
            "android": self.shell("getprop ro.build.version.release").strip(),
            "ram_total_mb": int(total.group(1)) // 1024 if total else 0,
            "disco_libre_kb": int(disco[3]) if len(disco) > 3 else 0,
        }

    def memoria_app(self) -> dict:
        salida = self.shell(f"dumpsys meminfo {PAQUETE}")
        def campo(patron: str) -> int:
            m = re.search(patron, salida)
            return int(m.group(1)) if m else 0
        return {
            "pss_total_mb": campo(r"TOTAL PSS:\s+(\d+)") // 1024,
            "native_heap_mb": campo(r"Native Heap\s+(\d+)") // 1024,
            "dalvik_heap_mb": campo(r"Dalvik Heap\s+(\d+)") // 1024,
        }

    def huella_disco(self) -> dict:
        pesos = self.shell(
            f"find {DIR_APP} -name '*.litertlm' -exec stat -c %s {{}} \\; 2>/dev/null"
        )
        tamanos = [int(x) for x in pesos.split() if x.isdigit()]
        cache = self.shell(
            f"du -sk /data/data/{PAQUETE}/cache 2>/dev/null || "
            f"du -sk /data/user/0/{PAQUETE}/cache 2>/dev/null"
        ).split()
        return {
            "binarios_litertlm": tamanos,
            "binario_mb": round(max(tamanos) / (1024 * 1024), 1) if tamanos else 0.0,
            "cache_mb": round(int(cache[0]) / 1024, 1) if cache and cache[0].isdigit() else 0.0,
        }


PATRONES_LOG = {
    "ttft_ms": re.compile(r"(?:ttft|time.to.first.token)\D{0,20}([\d.]+)", re.IGNORECASE),
    "tok_s": re.compile(r"([\d.]+)\s*(?:tokens?/s|tok/s|tps)", re.IGNORECASE),
    "prefill_ms": re.compile(r"prefill\D{0,20}([\d.]+)", re.IGNORECASE),
    "decode_ms": re.compile(r"decode\D{0,20}([\d.]+)", re.IGNORECASE),
}


def extraer_metricas(log: str) -> dict:
    salida: dict[str, float] = {}
    for nombre, patron in PATRONES_LOG.items():
        valores = [float(m) for m in patron.findall(log)]
        if valores:
            salida[nombre] = valores[-1]
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="Medicion on-device de eficiencia")
    ap.add_argument("--dispositivo", default="emulator-5554")
    ap.add_argument("--escenario", default="E1", choices=["E1", "E2", "E3"])
    ap.add_argument("--repeticiones", type=int, default=3)
    ap.add_argument("--espera", type=int, default=75,
                    help="Segundos de espera por respuesta")
    ap.add_argument("--output", default="results/ondevice_metricas.json")
    args = ap.parse_args()

    dev = Dispositivo(args.dispositivo)
    info = dev.info()
    print(f"[on-device] {info['modelo']} | Android {info['android']} | "
          f"{info['abi']} | RAM {info['ram_total_mb']} MB | "
          f"libre {info['disco_libre_kb'] // 1024} MB")

    if info["ram_total_mb"] < 5500:
        print(f"    AVISO: el dispositivo reporta {info['ram_total_mb']} MB de RAM. "
              "El plan de tesis exige 6 GB para evitar que el Low Memory Killer "
              "cierre la app durante la compilacion XNNPack.")
    if info["disco_libre_kb"] // 1024 < 8192:
        print(f"    AVISO: solo {info['disco_libre_kb'] // 1024} MB libres; "
              "se recomiendan 8192 MB.")

    print("[on-device] reiniciando la app")
    dev.shell(f"am force-stop {PAQUETE}")
    time.sleep(2)
    dev.ejecutar("shell", "am", "start", "-n", ACTIVIDAD)
    time.sleep(12)

    huella = dev.huella_disco()
    print(f"[on-device] binario {huella['binario_mb']} MB | "
          f"cache {huella['cache_mb']} MB")

    mediciones = []
    for i in range(args.repeticiones):
        consulta = CONSULTAS[i % len(CONSULTAS)]
        print(f"\n[{i + 1}/{args.repeticiones}] {consulta}")

        dev.ejecutar("logcat", "-c")
        inicio = time.perf_counter()

        # El texto se envia por teclado virtual: input text no acepta espacios.
        dev.shell(f"input text '{consulta.replace(' ', '%s')}'")
        time.sleep(1)
        dev.shell("input keyevent 66")  # Enter

        time.sleep(args.espera)
        transcurrido = (time.perf_counter() - inicio) * 1000

        log = dev.ejecutar("logcat", "-d")
        metricas = extraer_metricas(log)
        memoria = dev.memoria_app()
        vivo = bool(dev.shell(f"pidof {PAQUETE}").strip())

        registro = {
            "consulta": consulta,
            "escenario": args.escenario,
            "proceso_vivo": vivo,
            "latencia_observada_ms": transcurrido,
            "metricas_log": metricas,
            "memoria": memoria,
        }
        mediciones.append(registro)
        print(f"    proceso vivo={vivo} | PSS={memoria['pss_total_mb']} MB | "
              f"nativo={memoria['native_heap_mb']} MB | log={metricas or 'sin datos'}")

        if not vivo:
            print("    ATENCION: la app se cerro durante la inferencia.")
            break

    salida = Path(args.output)
    if not salida.is_absolute():
        salida = ROOT / salida
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(
        json.dumps(
            {
                "fecha": datetime.now(timezone.utc).isoformat(),
                "dispositivo": info,
                "huella_disco": huella,
                "escenario": args.escenario,
                "mediciones": mediciones,
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n[on-device] -> {salida.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
