import time
import logging
import threading
from datetime import datetime, timezone
import pandas as pd
import yfinance as yf
from . import config
from .indicators import enrich_indicators

log = logging.getLogger(__name__)
_cache = {}
_cache_lock = threading.Lock()

PERIODS = {"1m": "5d", "5m": "1mo", "15m": "60d", "1h": "730d"}

def _download(ticker: str, timeframe: str) -> pd.DataFrame:
    interval = config.TIMEFRAMES[timeframe]
    last_error = None
    for attempt in range(3):
        try:
            df = yf.download(
                tickers=ticker, period=PERIODS[timeframe], interval=interval,
                progress=False, auto_adjust=False, threads=False,
                timeout=config.MARKET_TIMEOUT
            )
            if df is None or df.empty:
                raise ValueError(f"Yahoo Finance no devolvió velas para {ticker} ({timeframe})")
            break
        except Exception as exc:
            last_error = exc
            if attempt == 2:
                raise RuntimeError(f"Falló la descarga tras 3 intentos: {type(exc).__name__}: {exc}") from exc
            time.sleep(0.7 * (attempt + 1))
    if isinstance(df.columns, pd.MultiIndex):
        # yfinance puede devolver columnas (Price, Ticker) o (Ticker, Price)
        if ticker in df.columns.get_level_values(-1):
            df.columns = df.columns.get_level_values(0)
        else:
            df.columns = df.columns.get_level_values(-1)
    required = {"Open", "High", "Low", "Close"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError("Yahoo Finance devolvió columnas incompletas: " + ", ".join(sorted(missing)))
    # Evita velas corruptas antes de calcular indicadores.
    df = df.copy()
    df = df[(pd.to_numeric(df["High"], errors="coerce") >= pd.to_numeric(df["Low"], errors="coerce"))]
    return df

def get_market_frame(ticker: str, timeframe: str, force: bool = False) -> pd.DataFrame:
    if timeframe not in config.TIMEFRAMES:
        raise ValueError(f"Temporalidad no admitida: {timeframe}")
    key = (ticker, timeframe)
    now = time.monotonic()
    with _cache_lock:
        cached = _cache.get(key)
        if not force and cached and now - cached[0] < config.CACHE_SECONDS:
            return cached[1].copy()
    raw = _download(ticker, timeframe)
    frame = enrich_indicators(raw)
    with _cache_lock:
        _cache[key] = (now, frame.copy())
    return frame

def clear_cache():
    with _cache_lock:
        _cache.clear()

def market_snapshot(ticker: str, timeframe: str, force: bool = False) -> dict:
    df = get_market_frame(ticker, timeframe, force=force)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    ts = df.index[-1]
    if getattr(ts, "tzinfo", None) is None:
        ts = ts.tz_localize("UTC")
    ts_utc = ts.to_pydatetime().astimezone(timezone.utc)
    age = max(0.0, (datetime.now(timezone.utc) - ts_utc).total_seconds() / 60)
    stale_limit = config.STALE_MINUTES.get(timeframe, 60)
    stale = age > stale_limit

    recent = df.tail(50)
    price = float(last["Close"])
    support = float(recent["Low"].min())
    resistance = float(recent["High"].max())
    candle_range = max(float(last["High"] - last["Low"]), 1e-12)
    atr_pct = float(last["ATR"]) / max(abs(price), 1e-12) * 100
    body = abs(float(last["Close"] - last["Open"]))
    return {
        "ticker": ticker, "timeframe": timeframe,
        "price": price, "open": float(last["Open"]),
        "high": float(last["High"]), "low": float(last["Low"]),
        "rsi": float(last["RSI"]),
        "macd": float(last["MACD"]),
        "macd_signal": float(last["MACD_SIGNAL"]),
        "macd_hist": float(last["MACD_HIST"]),
        "ema9": float(last["EMA9"]), "ema21": float(last["EMA21"]),
        "ema50": float(last["EMA50"]),
        "ema100": float(last["EMA100"]) if "EMA100" in df else None,
        "ema200": float(last["EMA200"]) if "EMA200" in df else None,
        "bb_high": float(last["BB_HIGH"]), "bb_low": float(last["BB_LOW"]),
        "bb_mid": float(last["BB_MID"]), "bb_width": float(last["BB_WIDTH"]),
        "atr": float(last["ATR"]), "adx": float(last["ADX"]),
        "cci": float(last["CCI"]), "stoch_k": float(last["STOCH_K"]),
        "stoch_d": float(last["STOCH_D"]), "roc": float(last["ROC"]),
        "support": support, "resistance": resistance,
        "mfi": float(last["MFI"]), "obv": float(last["OBV"]),
        "atr_pct": atr_pct,
        "volatility_regime": "ALTA" if atr_pct >= 2.0 else ("BAJA" if atr_pct <= 0.15 else "NORMAL"),
        "williams_r": float(last["WILLIAMS_R"]),
        "donchian_high": float(last["DONCHIAN_HIGH"]),
        "donchian_low": float(last["DONCHIAN_LOW"]),
        "change_pct": (price / float(prev["Close"]) - 1) * 100,
        "candle_bull": bool(last["Close"] > last["Open"]),
        "candle_bear": bool(last["Close"] < last["Open"]),
        "body_ratio": body / candle_range,
        "last_candle_utc": ts_utc.isoformat(),
        "age_minutes": round(age, 2), "stale": stale,
        "candles": len(df), "source": "Yahoo Finance"
    }
