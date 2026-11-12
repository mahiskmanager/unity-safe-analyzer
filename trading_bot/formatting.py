from datetime import datetime
from zoneinfo import ZoneInfo
from . import config

def fmt_price(value):
    if value is None:
        return "N/A"
    value = float(value)
    if abs(value) >= 1000:
        return f"{value:,.2f}"
    if abs(value) >= 1:
        return f"{value:.5f}".rstrip("0").rstrip(".")
    return f"{value:.8f}".rstrip("0").rstrip(".")

def analysis_message(result):
    s = result["snapshot"]
    a = result["technical"]
    direction = a["direction"]
    icon = {"CALL": "🟢", "PUT": "🔴", "NO_OPERAR": "⚪"}.get(direction, "⚪")
    reasons = "\n".join(f"• {x}" for x in a.get("reasons", [])[:8]) or "• Sin confirmaciones"
    confirm = result.get("confirmations") or {}
    confirm_text = "\n".join(
        f"• {tf}: {v.get('direction', 'ERROR')}"
        for tf, v in confirm.items()
    ) or "No solicitada"
    age = s["age_minutes"]
    stale_label = "⚠️ POSIBLEMENTE RETRASADO" if s["stale"] else "Edad de vela verificada"
    msg = f"""
📊 TRADING AI ANALYZER PRO
━━━━━━━━━━━━━━━━━━
Activo: {result['asset']}
Temporalidad: {result['timeframe']}
Fuente: {s['source']}
Última vela UTC: {s['last_candle_utc']}
Edad de vela: {age:.1f} min — {stale_label}

💰 Precio de referencia: {fmt_price(s['price'])}
Cambio vela: {s['change_pct']:.3f}%

📈 INDICADORES
RSI(14): {s['rsi']:.2f}
MACD: {s['macd']:.6f}
MACD señal: {s['macd_signal']:.6f}
EMA 9 / 21 / 50 / 100: {fmt_price(s['ema9'])} / {fmt_price(s['ema21'])} / {fmt_price(s['ema50'])} / {fmt_price(s.get('ema100'))}
ADX(14): {s['adx']:.2f}
MFI(14): {s.get('mfi', 50):.2f}
Williams %R: {s.get('williams_r', 0):.2f}
ATR(14): {fmt_price(s['atr'])}
CCI: {s['cci']:.1f}
Stoch RSI K/D: {s['stoch_k']:.2f}/{s['stoch_d']:.2f}
Bollinger superior/inferior: {fmt_price(s['bb_high'])} / {fmt_price(s['bb_low'])}

📍 Rango reciente
Soporte: {fmt_price(s['support'])}
Resistencia: {fmt_price(s['resistance'])}

━━━━━━━━━━━━━━━━━━
{icon} DECISIÓN TÉCNICA: {direction}
Índice de confluencia: {a['confidence']}/100
Puntuación CALL/PUT: {a['bull_score']}/{a['bear_score']}
Riesgo cualitativo: {a['risk']}

Entrada de referencia: {fmt_price(a.get('entry'))}
Stop técnico orientativo: {fmt_price(a.get('stop'))}
Objetivo técnico orientativo: {fmt_price(a.get('target'))}

Confirmación multi-temporal:
{confirm_text}

Fundamentos:
{reasons}
"""
    if result.get("explanation"):
        msg += "\n🧠 EXPLICACIÓN IA\n" + result["explanation"] + "\n"
    msg += (
        "\n⚠️ Informativo, no asesoría ni orden. "
        "La puntuación NO es probabilidad de éxito. "
        "Yahoo Finance puede retrasar datos. Verifica spread y ejecución."
    )
    return msg[:3900]

def signal_keyboard(signal_id):
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🟢 WIN", callback_data=f"RESULT:WIN:{signal_id}"),
        InlineKeyboardButton("🔴 LOSS", callback_data=f"RESULT:LOSS:{signal_id}"),
        InlineKeyboardButton("⚪ VOID", callback_data=f"RESULT:VOID:{signal_id}")
    ]])
