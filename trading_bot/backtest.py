"""Backtest OHLC conservador, sin look-ahead y con costos simulados."""
from __future__ import annotations
import math
import pandas as pd


def run_backtest(frame: pd.DataFrame, initial_capital: float = 1000.0,
                 risk_pct: float = 1.0, fee_bps: float = 2.0,
                 slippage_bps: float = 1.0, stop_atr: float = 1.5,
                 target_atr: float = 2.0) -> dict:
    required = {"Open", "High", "Low", "Close", "EMA9", "EMA21", "EMA50", "RSI", "MACD", "MACD_SIGNAL", "ADX", "ATR"}
    if frame is None or len(frame) < 100:
        raise ValueError("El backtest necesita al menos 100 velas con indicadores.")
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError("Faltan columnas: " + ", ".join(sorted(missing)))
    if initial_capital <= 0 or not 0 < risk_pct <= 5:
        raise ValueError("Capital inválido o riesgo fuera del rango 0-5%.")
    if min(fee_bps, slippage_bps) < 0 or min(stop_atr, target_atr) <= 0:
        raise ValueError("Costos no negativos y multiplicadores ATR positivos requeridos.")

    cash = float(initial_capital)
    equity = [cash]
    trades: list[dict] = []
    position = None

    # La señal se obtiene de la vela anterior y se ejecuta en la apertura actual.
    for i in range(61, len(frame)):
        signal = frame.iloc[i - 1]
        bar = frame.iloc[i]
        if position is None:
            rsi = float(signal.RSI)
            adx = float(signal.ADX)
            bull = (signal.EMA9 > signal.EMA21 > signal.EMA50 and 52 < rsi < 70
                    and signal.MACD > signal.MACD_SIGNAL and adx >= 20)
            bear = (signal.EMA9 < signal.EMA21 < signal.EMA50 and 30 < rsi < 48
                    and signal.MACD < signal.MACD_SIGNAL and adx >= 20)
            atr = float(signal.ATR)
            if (bull or bear) and math.isfinite(atr) and atr > 0:
                direction = 1 if bull else -1
                entry = float(bar.Open) * (1 + direction * slippage_bps / 10000)
                stop = entry - direction * atr * stop_atr
                target = entry + direction * atr * target_atr
                risk_cash = cash * risk_pct / 100
                qty = risk_cash / max(abs(entry - stop), 1e-12)
                position = {"direction": direction, "entry": entry, "stop": stop,
                            "target": target, "qty": qty, "opened": str(frame.index[i])}

        if position is not None:
            hi, lo = float(bar.High), float(bar.Low)
            d = position["direction"]
            stop_hit = lo <= position["stop"] if d == 1 else hi >= position["stop"]
            target_hit = hi >= position["target"] if d == 1 else lo <= position["target"]
            exit_price, reason = None, ""
            # Si stop y objetivo caben en una misma vela, se contabiliza primero el stop.
            if stop_hit:
                exit_price, reason = position["stop"], "STOP"
            elif target_hit:
                exit_price, reason = position["target"], "TARGET"
            elif i == len(frame) - 1:
                exit_price, reason = float(bar.Close), "END_OF_DATA"
            if exit_price is not None:
                exit_price *= (1 - d * slippage_bps / 10000)
                gross = (exit_price - position["entry"]) * d * position["qty"]
                fees = (abs(position["entry"] * position["qty"]) + abs(exit_price * position["qty"])) * fee_bps / 10000
                pnl = gross - fees
                cash += pnl
                trades.append({**position, "closed": str(frame.index[i]), "exit": exit_price,
                               "reason": reason, "pnl": pnl,
                               "return_pct": pnl / initial_capital * 100})
                position = None
        equity.append(cash)

    wins = [t for t in trades if t["pnl"] > 0]
    losses = [t for t in trades if t["pnl"] <= 0]
    peak, max_dd = initial_capital, 0.0
    for value in equity:
        peak = max(peak, value)
        if peak:
            max_dd = max(max_dd, (peak - value) / peak * 100)
    gross_profit = sum(t["pnl"] for t in wins)
    gross_loss = abs(sum(t["pnl"] for t in losses))
    return {"initial_capital": initial_capital, "final_capital": cash,
            "net_pnl": cash - initial_capital, "trades": len(trades),
            "wins": len(wins), "losses": len(losses),
            "win_rate": len(wins) / len(trades) * 100 if trades else 0.0,
            "profit_factor": gross_profit / gross_loss if gross_loss else (math.inf if gross_profit else 0),
            "max_drawdown_pct": max_dd,
            "avg_trade": sum(t["pnl"] for t in trades) / len(trades) if trades else 0,
            "fees_bps_per_side": fee_bps, "slippage_bps_per_side": slippage_bps,
            "trades_detail": trades[-30:]}
