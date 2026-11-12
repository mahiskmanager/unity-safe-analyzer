import asyncio
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, InputFile
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

from . import config
from .config import ASSETS, TIMEFRAMES, validate_config
from .storage import (
    init_db, add_signal, set_result, recent_signals,
    statistics, export_csv
)
from .analyzer import analyze
from .formatting import analysis_message, signal_keyboard
from .scanner import scan_once, scanner_loop
from .ai import list_models
from .market import get_market_frame
from .patterns import detect_patterns
from .risk import position_size
from .backtest import run_backtest
from .diagnostics import diagnose

log = logging.getLogger(__name__)

def authorized(update: Update) -> bool:
    return (
        update.effective_chat is not None
        and update.effective_chat.type == "private"
        and update.effective_user is not None
        and str(update.effective_chat.id) == config.ADMIN_CHAT_ID
    )

async def deny(update):
    if update.effective_message:
        await update.effective_message.reply_text("⛔ No autorizado.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not authorized(update):
        return await deny(update)
    await update.effective_message.reply_text(
        "🤖 TRADING AI ANALYZER PRO 3.0\n\n"
        "/analizar EUR/USD 5m\n/scan\n/auto_on\n/auto_off\n"
        "/activos\n/timeframes\n/senales\n/stats\n/stats_hoy\n"
        "/riesgo\n/calcriesgo capital riesgo_pct entrada stop [valor_punto]\n"
        "/patrones EUR/USD 5m\n/backtest EUR/USD 5m [capital]\n/health\n"
        "/exportar\n/modelos\n/status\n\n"
        "Solo DM privado del administrador. Análisis informativo; no ejecuta operaciones."
    )

async def status(update, context):
    if not authorized(update): return await deny(update)
    auto = context.application.bot_data.get("auto_scan", False)
    await update.effective_message.reply_text(
        f"Estado: ONLINE\n"
        f"Escáner automático: {'ACTIVO' if auto else 'INACTIVO'}\n"
        f"Proveedor: Yahoo Finance (datos sujetos a retraso y límites)\n"
        f"Groq: {'ACTIVO' if config.GROQ_ENABLED else 'DESACTIVADO'}\n"
        f"Modelo configurado: {config.GROQ_MODEL if config.GROQ_ENABLED else 'N/A'}\n"
        f"Temporalidad escáner: {config.DEFAULT_TIMEFRAME}\n"
        f"Intervalo: {config.SCAN_INTERVAL_SECONDS}s"
    )

async def activos(update, context):
    if not authorized(update): return await deny(update)
    await update.effective_message.reply_text(
        "ACTIVOS\n" + "\n".join(f"• {a} — {t}" for a, t in ASSETS.items())
    )

async def timeframes(update, context):
    if not authorized(update): return await deny(update)
    await update.effective_message.reply_text(
        "Temporalidades: " + ", ".join(TIMEFRAMES)
    )

async def analizar(update, context):
    if not authorized(update): return await deny(update)
    if len(context.args) < 2:
        return await update.effective_message.reply_text(
            "Uso: /analizar EUR/USD 5m"
        )
    asset = context.args[0].upper()
    timeframe = context.args[1].lower()
    ticker_to_asset = {v.upper(): k for k, v in ASSETS.items()}
    if asset in ticker_to_asset:
        asset = ticker_to_asset[asset]
    if asset not in ASSETS:
        return await update.effective_message.reply_text(
            "Activo no permitido. Usa /activos."
        )
    if timeframe not in TIMEFRAMES:
        return await update.effective_message.reply_text(
            "Temporalidad no válida. Usa /timeframes."
        )
    msg = await update.effective_message.reply_text("⏳ Consultando mercado...")
    try:
        result = await analyze(asset, ASSETS[asset], timeframe)
        tech = result["technical"]
        keyboard = None
        if tech["direction"] in {"CALL", "PUT"}:
            sid = add_signal(asset, ASSETS[asset], timeframe, result["snapshot"], tech)
            keyboard = signal_keyboard(sid)
        await msg.edit_text(analysis_message(result), reply_markup=keyboard)
    except Exception as exc:
        log.exception("Error en análisis %s", asset)
        await msg.edit_text(f"❌ No se pudo analizar {asset}:\n{str(exc)[:700]}")

async def scan(update, context):
    if not authorized(update): return await deny(update)
    msg = await update.effective_message.reply_text("🔎 Escaneando mercados...")
    results = await scan_once()
    if not results:
        return await msg.edit_text("⚪ No se encontraron configuraciones que superen los filtros.")
    await msg.edit_text(f"Escaneo terminado: {len(results)} configuraciones.")
    for result in results:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=analysis_message(result),
            reply_markup=signal_keyboard(result["signal_id"])
        )

async def auto_on(update, context):
    if not authorized(update): return await deny(update)
    app = context.application
    if app.bot_data.get("auto_scan", False):
        return await update.effective_message.reply_text("El escáner ya está activo.")
    app.bot_data["auto_scan"] = True
    task = app.create_task(scanner_loop(app), name="trading-auto-scanner")
    app.bot_data["scanner_task"] = task
    await update.effective_message.reply_text(
        f"✅ Escáner activado. Intervalo: {config.SCAN_INTERVAL_SECONDS}s."
    )

async def auto_off(update, context):
    if not authorized(update): return await deny(update)
    app = context.application
    app.bot_data["auto_scan"] = False
    task = app.bot_data.get("scanner_task")
    if task and not task.done():
        task.cancel()
    await update.effective_message.reply_text("🛑 Escáner automático detenido.")

async def callback_result(update, context):
    query = update.callback_query
    if not authorized(update):
        return await query.answer("No autorizado", show_alert=True)
    try:
        _, result, signal_id = query.data.split(":", 2)
    except ValueError:
        return await query.answer("Acción inválida", show_alert=True)
    if result not in {"WIN", "LOSS", "VOID"}:
        return await query.answer("Resultado inválido", show_alert=True)
    changed = set_result(signal_id, result)
    if not changed:
        return await query.answer("Señal inexistente o ya cerrada", show_alert=True)
    await query.answer("Resultado guardado")
    await query.edit_message_reply_markup(reply_markup=None)
    await query.message.reply_text(f"Resultado registrado: {result}")

async def senales(update, context):
    if not authorized(update): return await deny(update)
    rows = recent_signals(10)
    if not rows:
        return await update.effective_message.reply_text("No hay señales guardadas.")
    lines = ["ÚLTIMAS SEÑALES"]
    for r in rows:
        lines.append(
            f"{r['created_at'][:16]} | {r['asset']} {r['timeframe']} | "
            f"{r['direction']} {r['confidence']} | {r['result']} | ID {r['id']}"
        )
    await update.effective_message.reply_text("\n".join(lines)[:3900])

async def stats_common(update, today=False):
    s = statistics(today=today)
    title = "ESTADÍSTICAS DE HOY" if today else "ESTADÍSTICAS GENERALES"
    await update.effective_message.reply_text(
        f"📊 {title}\nTotal: {s['total']}\n"
        f"🟢 WIN: {s['wins']}\n🔴 LOSS: {s['losses']}\n"
        f"⚪ VOID: {s['void']}\n🟡 Pendientes: {s['pending']}\n"
        f"Cerradas: {s['closed']}\nAcierto manual: {s['accuracy']:.1f}%"
    )

async def stats(update, context):
    if not authorized(update): return await deny(update)
    await stats_common(update, False)

async def stats_hoy(update, context):
    if not authorized(update): return await deny(update)
    await stats_common(update, True)

async def riesgo(update, context):
    if not authorized(update): return await deny(update)
    await update.effective_message.reply_text(
        "GESTIÓN DE RIESGO\n\n"
        "• El tamaño de posición debe calcularse según capital, distancia al stop y valor del punto.\n"
        "• Evita martingala y sobreexposición correlacionada.\n"
        "• Considera spread, comisiones, deslizamiento y noticias.\n"
        "• No uses una puntuación heurística como probabilidad de éxito.\n"
        "• Prueba en demo y realiza backtesting antes de operar.\n"
        "• Los niveles mostrados son referencias, no órdenes."
    )

async def exportar(update, context):
    if not authorized(update): return await deny(update)
    content = export_csv()
    if not content.strip():
        return await update.effective_message.reply_text("Historial vacío.")
    import io
    file = InputFile(io.BytesIO(content.encode("utf-8")), filename="trading_signals.csv")
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=file,
        caption="Historial de señales (resultados manuales)."
    )

async def modelos(update, context):
    if not authorized(update): return await deny(update)
    try:
        models = await list_models()
        text = "MODELOS GROQ DISPONIBLES\n" + "\n".join("• " + m for m in models[:60])
        await update.effective_message.reply_text(text[:3900])
    except Exception as exc:
        await update.effective_message.reply_text(f"No se pudieron consultar modelos: {str(exc)[:500]}")


async def patrones(update, context):
    if not authorized(update): return await deny(update)
    if len(context.args) < 2:
        return await update.effective_message.reply_text("Uso: /patrones EUR/USD 5m")
    asset, timeframe = context.args[0].upper(), context.args[1].lower()
    if asset not in ASSETS or timeframe not in TIMEFRAMES:
        return await update.effective_message.reply_text("Activo o temporalidad inválidos. Usa /activos y /timeframes.")
    try:
        frame = await asyncio.to_thread(get_market_frame, ASSETS[asset], timeframe)
        found = detect_patterns(frame)
        lines = [f"PATRONES | {asset} | {timeframe}"]
        lines += [f"• {x['name']} — {x['bias']}\n  {x['detail']}" for x in found]
        await update.effective_message.reply_text("\n".join(lines)[:3900])
    except Exception as exc:
        await update.effective_message.reply_text(f"No se pudieron detectar patrones: {type(exc).__name__}: {str(exc)[:300]}")

async def backtest_cmd(update, context):
    if not authorized(update): return await deny(update)
    if len(context.args) < 2:
        return await update.effective_message.reply_text("Uso: /backtest EUR/USD 5m [capital]")
    asset, timeframe = context.args[0].upper(), context.args[1].lower()
    if asset not in ASSETS or timeframe not in TIMEFRAMES:
        return await update.effective_message.reply_text("Activo o temporalidad inválidos.")
    try:
        capital = float(context.args[2]) if len(context.args) > 2 else 1000.0
        frame = await asyncio.to_thread(get_market_frame, ASSETS[asset], timeframe, True)
        report = await asyncio.to_thread(run_backtest, frame, capital)
        pf = report['profit_factor']
        pf_text = f"{pf:.2f}" if pf != float('inf') else "∞"
        text = (f"BACKTEST HISTÓRICO — {asset} {timeframe}\n"
                f"Capital inicial: {report['initial_capital']:.2f}\n"
                f"Capital final: {report['final_capital']:.2f}\n"
                f"P/L neto: {report['net_pnl']:.2f}\n"
                f"Operaciones: {report['trades']} | WIN: {report['wins']} | LOSS: {report['losses']}\n"
                f"Win rate: {report['win_rate']:.1f}%\nProfit factor: {pf_text}\n"
                f"Drawdown máximo: {report['max_drawdown_pct']:.2f}%\n"
                f"Promedio por trade: {report['avg_trade']:.2f}\n"
                f"Costos simulados: {report['fees_bps_per_side']} bps comisión + {report['slippage_bps_per_side']} bps deslizamiento por lado.\n"
                "Nota: simulación OHLC, no predicción; no garantiza resultados futuros.")
        await update.effective_message.reply_text(text[:3900])
    except Exception as exc:
        await update.effective_message.reply_text(f"Backtest fallido: {type(exc).__name__}: {str(exc)[:350]}")

async def calcriesgo(update, context):
    if not authorized(update): return await deny(update)
    if len(context.args) not in {4, 5}:
        return await update.effective_message.reply_text("Uso: /calcriesgo capital riesgo_pct entrada stop [valor_punto]")
    try:
        capital, pct, entry, stop = map(float, context.args[:4])
        point = float(context.args[4]) if len(context.args) == 5 else 1.0
        calc = position_size(capital, pct, entry, stop, point)
        await update.effective_message.reply_text(
            f"CALCULADORA DE RIESGO\nCapital: {capital:.2f}\nRiesgo: {pct:.2f}% = {calc['risk_cash']:.2f}\n"
            f"Distancia al stop: {calc['distance']:.6f}\nUnidades teóricas: {calc['units']:.6f}\n"
            f"Notional aproximado: {calc['notional']:.2f}\n\nAjusta valor del punto, contrato, apalancamiento y tamaño mínimo del broker."
        )
    except Exception as exc:
        await update.effective_message.reply_text(f"Cálculo inválido: {str(exc)[:300]}")

async def health(update, context):
    if not authorized(update): return await deny(update)
    data = await diagnose(context.bot)
    text = "DIAGNÓSTICO DEL SISTEMA\n" + "\n".join(f"{k}: {v}" for k, v in data.items())
    await update.effective_message.reply_text(text[:3900])

async def error_handler(update, context):
    log.error("Error procesando actualización", exc_info=context.error)

async def post_init(application):
    if config.AUTO_SCAN_ENABLED:
        application.bot_data["auto_scan"] = True
        application.bot_data["scanner_task"] = application.create_task(
            scanner_loop(application), name="trading-auto-scanner"
        )

def run():
    config.validate_config()
    config.LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            RotatingFileHandler(config.LOG_PATH, maxBytes=2_000_000, backupCount=4, encoding="utf-8"),
            logging.StreamHandler()
        ],
        force=True
    )
    init_db()
    log.info("Iniciando Trading AI Analyzer Pro")
    app = (Application.builder().token(config.TOKEN)
           .concurrent_updates(False).post_init(post_init).build())
    handlers = [
        ("start", start), ("status", status), ("analizar", analizar),
        ("scan", scan), ("auto_on", auto_on), ("auto_off", auto_off),
        ("activos", activos), ("timeframes", timeframes),
        ("senales", senales), ("stats", stats), ("stats_hoy", stats_hoy),
        ("riesgo", riesgo), ("calcriesgo", calcriesgo), ("patrones", patrones),
        ("backtest", backtest_cmd), ("health", health),
        ("exportar", exportar), ("modelos", modelos)
    ]
    for command, callback in handlers:
        app.add_handler(CommandHandler(command, callback))
    app.add_handler(CallbackQueryHandler(callback_result, pattern=r"^RESULT:"))
    app.add_error_handler(error_handler)
    log.info("Bot listo. Chat administrador configurado.")
    app.run_polling(drop_pending_updates=True, allowed_updates=Update.ALL_TYPES)
