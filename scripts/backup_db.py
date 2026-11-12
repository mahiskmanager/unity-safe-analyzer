#!/usr/bin/env python3
"""Crea una copia consistente de la base SQLite sin detener el bot."""
from datetime import datetime
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trading_bot import config


def main():
    source = config.DATABASE_PATH
    if not source.exists():
        raise SystemExit(f"No existe la base de datos: {source}")
    target_dir = ROOT / 'backups'
    target_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    target = target_dir / f'signals_{stamp}.sqlite3'
    with sqlite3.connect(source) as src, sqlite3.connect(target) as dst:
        src.backup(dst)
    try:
        target.chmod(0o600)
    except OSError:
        pass
    print(f"Copia creada: {target.relative_to(ROOT)}")

if __name__ == '__main__':
    main()
