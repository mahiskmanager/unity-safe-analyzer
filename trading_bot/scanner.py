import asyncio
import logging
import time
from . import config
from .analyzer import analyze
from .storage import add_signal

log = logging.getLogger(__name__)
_last_alert = {}

async def scan_once():
    results = []
    for asset, ticker in config.ASSETS.items():
        try:
            result = await analyze(
                asset, ticker, config.DEFAULT_TIMEFRAME
            )
            tech = result["technical"]
            if (
                tech["direction"] in {"CALL", "PUT"}
                and tech["confidence"] >= config.SCAN_MIN_CONFIDENCE
            ):
                key = (asset, config.DEFAULT_TIMEFRAME, tech["direction"])
                now = time.monotonic()
                if now - _last_alert.get(key, 0) >= config.SCAN_COOLDOWN_SECONDS:
                    sid = add_signal(
                        asset, ticker, config.DEFAULT_TIMEFRAME,
                        result["snapshot"], tech
                    )
                    _last_alert[key] = now
                    result["signal_id"] = sid
                    results.append(result)
        except Exception:
            log.exception("Fallo escaneando %s", asset)
        await asyncio.sleep(0.5)
    results.sort(
        key=lambda x: x["technical"]["confidence"], reverse=True
    )
    return results[:config.MAX_SCAN_ALERTS]

async def scanner_loop(application):
    log.info("Escáner automático iniciado")
    while application.bot_data.get("auto_scan", False):
        try:
            results = await scan_once()
            chat_id = int(config.ADMIN_CHAT_ID)
            for result in results:
                from .formatting import analysis_message, signal_keyboard
                await application.bot.send_message(
                    chat_id=chat_id,
                    text="🔔 ALERTA AUTOMÁTICA\n" + analysis_message(result),
                    reply_markup=signal_keyboard(result["signal_id"])
                )
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("Error en ciclo automático")
        await asyncio.sleep(config.SCAN_INTERVAL_SECONDS)
    log.info("Escáner automático detenido")
