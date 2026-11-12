import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

def _bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "si", "sí"}

def _int(name: str, default: int, minimum: int = 1) -> int:
    try:
        return max(minimum, int(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default

def _float(name: str, default: float, minimum: float = 0.0) -> float:
    try:
        return max(minimum, float(os.getenv(name, str(default))))
    except (TypeError, ValueError):
        return default

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
GROQ_ENABLED = _bool("GROQ_ENABLED", False)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b").strip()
GROQ_TIMEOUT = _int("GROQ_TIMEOUT", 35)
TIMEZONE = os.getenv("TIMEZONE", "America/Guatemala")
DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "5m").lower()
CACHE_SECONDS = _int("CACHE_SECONDS", 25)
MARKET_TIMEOUT = _int("MARKET_TIMEOUT", 25)
MIN_CANDLES = _int("MIN_CANDLES", 80, 60)
AUTO_SCAN_ENABLED = _bool("AUTO_SCAN_ENABLED", False)
SCAN_INTERVAL_SECONDS = _int("SCAN_INTERVAL_SECONDS", 180, 30)
SCAN_MIN_CONFIDENCE = _int("SCAN_MIN_CONFIDENCE", 68, 1)
SCAN_COOLDOWN_SECONDS = _int("SCAN_COOLDOWN_SECONDS", 900, 60)
MULTI_TIMEFRAME_CONFIRMATION = _bool("MULTI_TIMEFRAME_CONFIRMATION", True)
MAX_SCAN_ALERTS = _int("MAX_SCAN_ALERTS", 3)
MIN_SCORE = _int("MIN_SCORE", 6, 1)
MIN_SCORE_GAP = _int("MIN_SCORE_GAP", 2, 1)
ATR_STOP_MULTIPLIER = _float("ATR_STOP_MULTIPLIER", 1.5, 0.1)
ATR_TARGET_MULTIPLIER = _float("ATR_TARGET_MULTIPLIER", 2.0, 0.1)
DATABASE_PATH = ROOT / os.getenv("DATABASE_PATH", "data/signals.sqlite3")
LOG_PATH = ROOT / os.getenv("LOG_PATH", "logs/bot.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

STALE_MINUTES = {
    "1m": _int("MAX_STALE_MINUTES_1M", 15),
    "5m": _int("MAX_STALE_MINUTES_5M", 30),
    "15m": _int("MAX_STALE_MINUTES_15M", 60),
    "1h": _int("MAX_STALE_MINUTES_1H", 180),
}

ASSETS = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "JPY=X",
    "XAU/USD": "GC=F",
    "BTC/USD": "BTC-USD",
    "ETH/USD": "ETH-USD",
    "SPX500": "^GSPC",
    "NASDAQ": "^IXIC",
    "USOIL": "CL=F",
}

TIMEFRAMES = {"1m": "1m", "5m": "5m", "15m": "15m", "1h": "60m"}

def validate_config():
    if not TOKEN:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN en .env")
    if not ADMIN_CHAT_ID:
        raise RuntimeError("Falta ADMIN_CHAT_ID en .env")
    if GROQ_ENABLED and not GROQ_API_KEY:
        raise RuntimeError("GROQ_ENABLED=true pero falta GROQ_API_KEY")
    if DEFAULT_TIMEFRAME not in TIMEFRAMES:
        raise RuntimeError(f"DEFAULT_TIMEFRAME inválido: {DEFAULT_TIMEFRAME}")
