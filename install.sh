#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

if ! command -v python >/dev/null 2>&1; then
  echo "Python no está instalado. Ejecuta: pkg install python git -y"
  exit 1
fi
python - <<'PY'
import sys
if sys.version_info < (3, 10):
    raise SystemExit("Se requiere Python 3.10 o superior.")
print(f"Python {sys.version.split()[0]} detectado.")
PY

mkdir -p data logs
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python setup_config.py

echo
echo "Instalación lista. Inicia con: python run.py"
echo "Edita credenciales con: python setup_config.py --edit"
