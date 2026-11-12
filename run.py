#!/usr/bin/env python3
"""Punto de entrada: configura credenciales antes de cargar el bot."""
from setup_config import configure

if __name__ == "__main__":
    configure()
    from trading_bot.handlers import run
    run()
