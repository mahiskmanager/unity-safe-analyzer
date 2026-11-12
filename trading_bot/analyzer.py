import asyncio
from . import config
from .market import market_snapshot
from .strategies import evaluate
from .ai import explain_with_groq

async def analyze(asset: str, ticker: str, timeframe: str, multi: bool | None = None):
    snapshot = await asyncio.to_thread(market_snapshot, ticker, timeframe)
    technical = evaluate(snapshot)

    use_multi = config.MULTI_TIMEFRAME_CONFIRMATION if multi is None else multi
    confirmations = {}
    if use_multi and timeframe in {"1m", "5m"}:
        higher = "5m" if timeframe == "1m" else "15m"
        try:
            higher_snapshot = await asyncio.to_thread(
                market_snapshot, ticker, higher
            )
            higher_result = evaluate(higher_snapshot)
            confirmations[higher] = {
                "direction": higher_result["direction"],
                "confidence": higher_result["confidence"],
                "stale": higher_snapshot["stale"]
            }
            if technical["direction"] in {"CALL", "PUT"}:
                if higher_result["direction"] != technical["direction"] or higher_snapshot["stale"]:
                    technical = dict(technical)
                    technical["direction"] = "NO_OPERAR"
                    technical["confidence"] = min(49, technical["confidence"])
                    technical["status"] = "MTF_NOT_CONFIRMED"
                    technical["reasons"] = technical["reasons"] + [
                        f"sin confirmación en {higher}"
                    ]
                    technical["entry"] = technical["stop"] = technical["target"] = None
        except Exception as exc:
            confirmations[higher] = {"error": str(exc)[:200]}
            if technical["direction"] in {"CALL", "PUT"}:
                technical = dict(technical)
                technical["direction"] = "NO_OPERAR"
                technical["confidence"] = min(49, technical["confidence"])
                technical["status"] = "MTF_UNAVAILABLE"
                technical["reasons"] = technical["reasons"] + [
                    f"confirmación {higher} no disponible"
                ]
                technical["entry"] = technical["stop"] = technical["target"] = None

    explanation = await explain_with_groq(snapshot, technical)
    return {
        "asset": asset, "ticker": ticker, "timeframe": timeframe,
        "snapshot": snapshot, "technical": technical,
        "confirmations": confirmations, "explanation": explanation
    }
