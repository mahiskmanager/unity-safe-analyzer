import asyncio
import json
import logging
import requests
from . import config

log = logging.getLogger(__name__)
URL = "https://api.groq.com/openai/v1/chat/completions"

async def explain_with_groq(snapshot: dict, technical: dict) -> str | None:
    if not config.GROQ_ENABLED or not config.GROQ_API_KEY:
        return None
    system = (
        "Eres un asistente que explica datos técnicos financieros. "
        "No inventes datos, precios, noticias ni probabilidades. "
        "No cambies la dirección calculada por el motor determinista. "
        "Si direction es NO_OPERAR, no propongas entrada. "
        "Responde en español, máximo 120 palabras, con riesgos y limitaciones."
    )
    user = {"market": snapshot, "technical_engine": technical}
    payload = {
        "model": config.GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)}
        ],
        "temperature": 0.1,
        "max_completion_tokens": 450,
        "response_format": {"type": "json_object"}
    }
    payload["messages"][0]["content"] += (
        ' Devuelve JSON con una única clave "explanation".'
    )

    def request():
        response = requests.post(
            URL,
            headers={
                "Authorization": f"Bearer {config.GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=config.GROQ_TIMEOUT
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Groq HTTP {response.status_code}: {response.text[:400]}"
            )
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return str(parsed.get("explanation", ""))[:1500]

    try:
        return await asyncio.to_thread(request)
    except Exception as exc:
        log.warning("Groq no disponible; se conserva análisis técnico: %s", exc)
        return None

async def list_models() -> list[str]:
    if not config.GROQ_API_KEY:
        raise RuntimeError("Configura GROQ_API_KEY en .env")

    def request():
        r = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
            timeout=config.GROQ_TIMEOUT
        )
        r.raise_for_status()
        return sorted(x["id"] for x in r.json().get("data", []))

    return await asyncio.to_thread(request)
