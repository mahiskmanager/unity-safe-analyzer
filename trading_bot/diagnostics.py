"""Diagnóstico básico de entorno y servicios."""
import asyncio
import platform
import requests
from . import config

async def diagnose(bot) -> dict:
    result = {"python": platform.python_version(), "platform": platform.platform(),
              "database": str(config.DATABASE_PATH), "telegram": "PENDIENTE",
              "groq": "DESACTIVADO" if not config.GROQ_ENABLED else "PENDIENTE"}
    try:
        me = await bot.get_me()
        result["telegram"] = f"OK (@{me.username or 'bot'})"
    except Exception as exc:
        result["telegram"] = f"ERROR: {type(exc).__name__}"
    if config.GROQ_ENABLED and config.GROQ_API_KEY:
        def ping():
            response = requests.get("https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"}, timeout=10)
            response.raise_for_status()
            return "OK"
        try:
            result["groq"] = await asyncio.to_thread(ping)
        except Exception as exc:
            result["groq"] = f"ERROR: {type(exc).__name__}"
    return result
