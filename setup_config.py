#!/usr/bin/env python3
"""Asistente interactivo para crear/actualizar credenciales del bot."""
from __future__ import annotations

import argparse
import getpass
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"


def read_existing() -> dict[str, str]:
    values: dict[str, str] = {}
    if not ENV_FILE.exists():
        return values
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def prompt_secret(label: str, current: str = "", required: bool = True) -> str:
    while True:
        suffix = " (deja vacío para conservar la actual)" if current else ""
        if not required:
            suffix += " (opcional; Enter para desactivar Groq)"
        value = getpass.getpass(f"{label}{suffix}: ").strip()
        if not value and current:
            return current
        if not value and not required:
            return ""
        if value:
            return value
        print("Este dato es obligatorio.")


def prompt_chat_id(current: str = "") -> str:
    while True:
        hint = f" (Enter conserva {current})" if current else ""
        value = input(f"ID numérico de Telegram{hint}: ").strip()
        if not value and current:
            return current
        if re.fullmatch(r"-?\d+", value):
            return value
        print("Introduce un ID numérico válido, por ejemplo 123456789 o -1001234567890.")


def write_env(values: dict[str, str]) -> None:
    # Conserva todas las opciones avanzadas que ya existan en .env.
    lines: list[str] = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    updates = {
        "TELEGRAM_BOT_TOKEN": values["TELEGRAM_BOT_TOKEN"],
        "ADMIN_CHAT_ID": values["ADMIN_CHAT_ID"],
        "GROQ_API_KEY": values["GROQ_API_KEY"],
        "GROQ_ENABLED": "true" if values["GROQ_API_KEY"] else "false",
    }
    seen: set[str] = set()
    output: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in updates:
                output.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        output.append(line)
    if output and output[-1].strip():
        output.append("")
    for key, value in updates.items():
        if key not in seen:
            output.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    try:
        ENV_FILE.chmod(0o600)
    except OSError:
        pass


def configure(force: bool = False) -> None:
    old = read_existing()
    if not force and old.get("TELEGRAM_BOT_TOKEN") and old.get("ADMIN_CHAT_ID") and old.get("GROQ_API_KEY"):
        return

    print("\n=== CONFIGURACIÓN INICIAL — TRADING AI ANALYZER PRO ===")
    print("Las claves se guardan localmente en .env y no se muestran en pantalla.\n")

    token = prompt_secret("Token del bot de Telegram (obtenido en @BotFather)", old.get("TELEGRAM_BOT_TOKEN", ""))
    if not re.fullmatch(r"\d+:[A-Za-z0-9_-]{20,}", token):
        print("Aviso: el formato del token no parece el habitual de Telegram. Se guardará, pero verifica que sea correcto.")

    chat_id = prompt_chat_id(old.get("ADMIN_CHAT_ID", ""))
    groq_key = prompt_secret("API Key de Groq (console.groq.com)", old.get("GROQ_API_KEY", ""), required=True)

    write_env({
        "TELEGRAM_BOT_TOKEN": token,
        "ADMIN_CHAT_ID": chat_id,
        "GROQ_API_KEY": groq_key,
    })
    print("\nConfiguración guardada correctamente en .env.")
    print("Groq: activado")
    print("Protección: .env tiene permisos privados y está excluido de Git.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Configurar credenciales del bot")
    parser.add_argument("--edit", action="store_true", help="volver a solicitar/actualizar las credenciales")
    args = parser.parse_args()
    try:
        configure(force=args.edit)
    except (KeyboardInterrupt, EOFError):
        print("\nConfiguración cancelada.", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
