"""Vérifie le lancement et l'état HTTP de l'exécutable, sans navigateur."""
from pathlib import Path
import subprocess
import sys
import time
from urllib.request import urlopen

exe = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / 'dist' / 'App_temperature.exe'
process = subprocess.Popen([str(exe), '--no-browser', '--port', '18731'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(120):
        if process.poll() is not None:
            raise RuntimeError(f"L'exécutable s'est arrêté : {process.returncode}")
        try:
            with urlopen('http://127.0.0.1:18731/_stcore/health', timeout=1) as response:
                if response.read() == b'ok':
                    print('Application accessible sur localhost.')
                    break
        except OSError:
            time.sleep(0.5)
    else:
        raise RuntimeError("L'application ne répond pas dans le délai prévu.")
finally:
    subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

