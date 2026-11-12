from . import config

def evaluate(snapshot: dict) -> dict:
    """Ensemble determinista. La puntuación es confluencia, no probabilidad."""
    p = snapshot
    bull = 0
    bear = 0
    reasons = []

    # Tendencia EMA
    if p["ema9"] > p["ema21"] > p["ema50"]:
        bull += 3
        reasons.append("alineación EMA alcista")
    elif p["ema9"] < p["ema21"] < p["ema50"]:
        bear += 3
        reasons.append("alineación EMA bajista")

    # EMA200 como filtro de régimen si está disponible
    if p.get("ema200") is not None:
        if p["price"] > p["ema200"]:
            bull += 1
        elif p["price"] < p["ema200"]:
            bear += 1

    # Momentum MACD
    if p["macd"] > p["macd_signal"] and p["macd_hist"] > 0:
        bull += 2
        reasons.append("MACD positivo")
    elif p["macd"] < p["macd_signal"] and p["macd_hist"] < 0:
        bear += 2
        reasons.append("MACD negativo")

    # RSI evita perseguir extremos
    if 52 <= p["rsi"] <= 68:
        bull += 1
    elif 32 <= p["rsi"] <= 48:
        bear += 1
    elif p["rsi"] > 75 or p["rsi"] < 25:
        reasons.append("RSI en zona extrema: penalizar entrada")

    # CCI y ROC
    if p["cci"] > 50 and p["roc"] > 0:
        bull += 1
    elif p["cci"] < -50 and p["roc"] < 0:
        bear += 1

    # Stochastic RSI: cruce aproximado y no extremo
    if p["stoch_k"] > p["stoch_d"] and p["stoch_k"] < 0.85:
        bull += 1
    elif p["stoch_k"] < p["stoch_d"] and p["stoch_k"] > 0.15:
        bear += 1

    # Flujo de dinero (MFI): confirmación secundaria, no señal autónoma.
    if p.get("mfi", 50) >= 55 and p["price"] > p["ema21"]:
        bull += 1
        reasons.append("MFI confirma presión compradora")
    elif p.get("mfi", 50) <= 45 and p["price"] < p["ema21"]:
        bear += 1
        reasons.append("MFI confirma presión vendedora")

    # ADX filtra fuerza de tendencia, sin dar dirección
    trend_strength = p["adx"] >= 20
    if trend_strength:
        reasons.append(f"ADX indica fuerza ({p['adx']:.1f})")

    # Vela actual, con peso moderado
    if p["candle_bull"] and p["body_ratio"] >= 0.45:
        bull += 1
    elif p["candle_bear"] and p["body_ratio"] >= 0.45:
        bear += 1

    # No operar con datos retrasados o ATR inválido
    if p["stale"]:
        return _neutral(bull, bear, reasons + ["datos posiblemente obsoletos"])
    if p["atr"] <= 0:
        return _neutral(bull, bear, reasons + ["ATR inválido"])
    if not trend_strength:
        reasons.append("ADX bajo: tendencia débil")

    gap = abs(bull - bear)
    if bull >= config.MIN_SCORE and bull - bear >= config.MIN_SCORE_GAP and trend_strength:
        direction = "CALL"
        score = bull
    elif bear >= config.MIN_SCORE and bear - bull >= config.MIN_SCORE_GAP and trend_strength:
        direction = "PUT"
        score = bear
    else:
        return _neutral(bull, bear, reasons + ["confluencia insuficiente"])

    # Índice heurístico, deliberadamente acotado y no probabilístico.
    confidence = min(90, max(50, int(50 + score * 4 + min(gap, 4) * 2)))
    entry = p["price"]
    stop_dist = p["atr"] * config.ATR_STOP_MULTIPLIER
    target_dist = p["atr"] * config.ATR_TARGET_MULTIPLIER

    if direction == "CALL":
        stop = entry - stop_dist
        target = entry + target_dist
    else:
        stop = entry + stop_dist
        target = entry - target_dist

    risk = "ALTO" if p["bb_width"] > 8 or p["adx"] < 25 or p.get("atr_pct", 0) >= 2 else "MEDIO"
    return {
        "direction": direction, "confidence": confidence,
        "bull_score": bull, "bear_score": bear,
        "reasons": reasons, "entry": entry,
        "stop": stop, "target": target,
        "risk": risk, "trend_strength": trend_strength,
        "status": "CANDIDATE"
    }

def _neutral(bull, bear, reasons):
    return {
        "direction": "NO_OPERAR", "confidence": min(49, 40 + max(bull, bear)),
        "bull_score": bull, "bear_score": bear,
        "reasons": reasons, "entry": None, "stop": None,
        "target": None, "risk": "ALTO",
        "trend_strength": False, "status": "FILTERED"
    }
