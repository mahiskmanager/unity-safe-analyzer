import pandas as pd
from ta.momentum import RSIIndicator, StochRSIIndicator, ROCIndicator
from ta.trend import MACD, EMAIndicator, ADXIndicator, CCIIndicator
from ta.volatility import BollingerBands, AverageTrueRange

REQUIRED = ["Open", "High", "Low", "Close"]

def enrich_indicators(raw: pd.DataFrame) -> pd.DataFrame:
    if raw is None or raw.empty:
        raise ValueError("No hay velas disponibles")
    df = raw.copy()
    for col in REQUIRED:
        if col not in df.columns:
            raise ValueError(f"Falta columna {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=REQUIRED).copy()
    if len(df) < 60:
        raise ValueError(f"Se requieren al menos 60 velas; recibidas: {len(df)}")

    close, high, low = df["Close"], df["High"], df["Low"]
    for period in (9, 21, 50, 100, 200):
        if len(df) >= period:
            df[f"EMA{period}"] = EMAIndicator(close, window=period).ema_indicator()
    df["RSI"] = RSIIndicator(close, window=14).rsi()
    macd = MACD(close, window_fast=12, window_slow=26, window_sign=9)
    df["MACD"] = macd.macd()
    df["MACD_SIGNAL"] = macd.macd_signal()
    df["MACD_HIST"] = macd.macd_diff()
    bb = BollingerBands(close, window=20, window_dev=2)
    df["BB_HIGH"] = bb.bollinger_hband()
    df["BB_LOW"] = bb.bollinger_lband()
    df["BB_MID"] = bb.bollinger_mavg()
    df["BB_WIDTH"] = bb.bollinger_wband()
    df["ATR"] = AverageTrueRange(high, low, close, window=14).average_true_range()
    df["ADX"] = ADXIndicator(high, low, close, window=14).adx()
    df["CCI"] = CCIIndicator(high, low, close, window=20).cci()
    stoch = StochRSIIndicator(close, window=14, smooth1=3, smooth2=3)
    df["STOCH_RSI"] = stoch.stochrsi()
    df["STOCH_K"] = stoch.stochrsi_k()
    df["STOCH_D"] = stoch.stochrsi_d()
    df["ROC"] = ROCIndicator(close, window=12).roc()
    df["RETURN"] = close.pct_change() * 100
    # Indicadores adicionales: flujo, rango y ubicación relativa.
    volume = pd.to_numeric(df.get("Volume", pd.Series(0, index=df.index)), errors="coerce").fillna(0)
    direction = close.diff().fillna(0).apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    df["OBV"] = (direction * volume).cumsum()
    typical = (high + low + close) / 3
    raw_flow = typical * volume
    pos_flow = raw_flow.where(typical.diff() > 0, 0).rolling(14).sum()
    neg_flow = raw_flow.where(typical.diff() < 0, 0).rolling(14).sum().abs()
    money_ratio = pos_flow / neg_flow.replace(0, pd.NA)
    df["MFI"] = (100 - (100 / (1 + money_ratio))).fillna(50)
    rolling_high = high.rolling(14).max()
    rolling_low = low.rolling(14).min()
    df["WILLIAMS_R"] = -100 * (rolling_high - close) / (rolling_high - rolling_low).replace(0, pd.NA)
    df["DONCHIAN_HIGH"] = high.rolling(20).max()
    df["DONCHIAN_LOW"] = low.rolling(20).min()
    df["DONCHIAN_MID"] = (df["DONCHIAN_HIGH"] + df["DONCHIAN_LOW"]) / 2
    df["CANDLE_RANGE"] = high - low
    df["BODY"] = (close - df["Open"]).abs()
    df["UPPER_WICK"] = high - df[["Open", "Close"]].max(axis=1)
    df["LOWER_WICK"] = df[["Open", "Close"]].min(axis=1) - low
    df = df.replace([float("inf"), float("-inf")], pd.NA).dropna().copy()
    if df.empty:
        raise ValueError("No hay suficientes datos para calcular indicadores")
    return df
