#!/usr/bin/env bash
set -euo pipefail
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
mkdir -p data logs
python setup_config.py
echo "Listo. Ejecuta: source .venv/bin/activate && python run.py"
