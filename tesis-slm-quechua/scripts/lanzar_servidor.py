from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def get_local_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main() -> None:
    ip_local = get_local_ip()
    api_port = 8000
    pwa_port = 3000

    print("=================================================================")
    print(" SERVIDOR ASISTENTE EIB QUECHUA COLLAO - NEXT.JS PWA + FASTAPI")
    print("=================================================================")
    print(f" Servidor Next.js PWA:      http://{ip_local}:{pwa_port}")
    print(f" Servidor API Backend Python: http://{ip_local}:{api_port}")
    print("=================================================================")
    print(" Presiona Ctrl+C para detener ambos servidores.\n")

    pwa_dir = ROOT / "apps" / "pwa"

    # 1. Iniciar Next.js en subproceso
    pwa_proc = subprocess.Popen(
        f"npx next start -H 0.0.0.0 -p {pwa_port}",
        cwd=str(pwa_dir),
        shell=True,
    )

    # 2. Iniciar FastAPI uvicorn
    import uvicorn

    try:
        uvicorn.run(
            "src.aplicacion.servidor_api:app",
            host="0.0.0.0",
            port=api_port,
            reload=False,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\nDeteniendo servidor API...")
    finally:
        pwa_proc.terminate()
        print("Servidores detenidos correctamente.")


if __name__ == "__main__":
    main()
