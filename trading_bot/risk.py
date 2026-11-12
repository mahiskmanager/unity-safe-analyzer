"""Cálculos educativos de exposición y relación riesgo/beneficio."""
from __future__ import annotations


def position_size(capital: float, risk_pct: float, entry: float, stop: float,
                  point_value: float = 1.0) -> dict:
    vals = (capital, risk_pct, entry, stop, point_value)
    if any(float(x) <= 0 for x in vals):
        raise ValueError("Todos los valores deben ser mayores que cero.")
    if risk_pct > 5:
        raise ValueError("El riesgo porcentual debe ser <= 5% en esta calculadora prudente.")
    distance = abs(entry - stop)
    if distance <= 0:
        raise ValueError("Entrada y stop no pueden ser iguales.")
    risk_cash = capital * risk_pct / 100
    units = risk_cash / (distance * point_value)
    return {"risk_cash": risk_cash, "distance": distance, "units": units,
            "notional": units * entry, "risk_pct": risk_pct}


def risk_reward(entry: float, stop: float, target: float) -> float:
    risk = abs(entry - stop)
    if risk == 0:
        raise ValueError("Distancia de stop inválida.")
    return abs(target - entry) / risk
