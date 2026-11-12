"""Reconocimiento de patrones de velas japonesas (reglas transparentes)."""
from __future__ import annotations
import pandas as pd


def detect_patterns(frame: pd.DataFrame) -> list[dict]:
    if frame is None or len(frame) < 3:
        return []
    cur, prev, prev2 = frame.iloc[-1], frame.iloc[-2], frame.iloc[-3]
    o, h, l, c = map(float, (cur.Open, cur.High, cur.Low, cur.Close))
    po, ph, pl, pc = map(float, (prev.Open, prev.High, prev.Low, prev.Close))
    rng = max(h - l, 1e-12)
    body = abs(c - o)
    upper = h - max(o, c)
    lower = min(o, c) - l
    out: list[dict] = []
    def add(name: str, bias: str, detail: str):
        out.append({"name": name, "bias": bias, "detail": detail})
    if body / rng <= 0.10:
        add("Doji", "NEUTRAL", "Apertura y cierre muy próximos; indecisión.")
    if lower >= body * 2.2 and upper <= max(body * 0.7, rng * 0.08) and body / rng < 0.4:
        add("Martillo / rechazo inferior", "BULLISH", "Mecha inferior larga; requiere confirmación posterior.")
    if upper >= body * 2.2 and lower <= max(body * 0.7, rng * 0.08) and body / rng < 0.4:
        add("Estrella fugaz / rechazo superior", "BEARISH", "Mecha superior larga; requiere confirmación posterior.")
    if c > o and pc < po and c >= po and o <= pc:
        add("Envolvente alcista", "BULLISH", "El cuerpo actual envuelve el cuerpo bajista previo.")
    if c < o and pc > po and c <= po and o >= pc:
        add("Envolvente bajista", "BEARISH", "El cuerpo actual envuelve el cuerpo alcista previo.")
    if h < ph and l > pl:
        add("Inside bar", "NEUTRAL", "Compresión dentro del rango anterior; vigilar ruptura.")
    p2o, p2c = float(prev2.Open), float(prev2.Close)
    prev_mid = (po + pc) / 2
    if p2c < p2o and c > o and c > prev_mid and abs(pc-po) > abs(p2c-p2o)*0.6:
        add("Posible giro alcista de 2 velas", "BULLISH", "Recuperación del punto medio del cuerpo anterior.")
    if p2c > p2o and c < o and c < prev_mid and abs(pc-po) > abs(p2c-p2o)*0.6:
        add("Posible giro bajista de 2 velas", "BEARISH", "Pérdida del punto medio del cuerpo anterior.")
    return out or [{"name": "Sin patrón destacado", "bias": "NEUTRAL", "detail": "No se detectó una figura definida en la última vela."}]
