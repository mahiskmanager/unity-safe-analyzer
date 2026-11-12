# Trading AI Analyzer Pro 3.0

Bot de Telegram para análisis técnico informativo. No ejecuta órdenes ni conecta con brokers.

## Funciones

- Análisis multi-activo y multi-temporalidad (1m, 5m, 15m, 1h).
- Indicadores: EMA 9/21/50/100/200, RSI, MACD, Bollinger Bands, ATR, ADX, Stochastic RSI, CCI, ROC, MFI, OBV, Williams %R y Donchian.
- Motor determinista de estrategias: tendencia, momentum, volatilidad, estructura y confirmación.
- Confirmación opcional multi-timeframe.
- Groq para explicar el contexto; la IA no puede convertir una señal técnica neutral en una entrada.
- Escáner manual y automático.
- Alertas con niveles técnicos orientativos (entrada de referencia, stop y objetivo por ATR).
- Registro SQLite de señales y resultados WIN/LOSS/VOID.
- Reconocimiento de patrones de velas: doji, martillo, rechazo superior, envolventes e inside bar.
- Backtesting OHLC con entrada en vela siguiente, costos simulados, win rate, profit factor y drawdown.
- Calculadora de riesgo, tamaño teórico de posición y diagnóstico de Telegram/Groq.
- Reintentos de descarga, validación de velas y logs rotativos.
- Estadísticas, filtros, exportación CSV y comandos administrativos.
- Protección por chat ID, configuración fuera del repositorio y logs sin credenciales.

## Requisitos

- Python 3.10 o superior (recomendado Python 3.11+).
- Cuenta/bot de Telegram y API key de Groq.
- Conexión a internet.
- Yahoo Finance puede retrasar, limitar o no proporcionar determinados intervalos/activos. No es una fuente de ejecución ni garantiza datos en tiempo real.

## Instalación rápida en Termux

```bash
pkg update -y
pkg install python git -y
git clone https://github.com/TU_USUARIO/trading-ai-analyzer-pro.git
cd trading-ai-analyzer-pro
bash install.sh
python run.py
```

Durante `bash install.sh` aparecerá un asistente que solicitará el token del bot, el ID numérico de tu chat y la API Key de Groq. Las claves se escribirán de forma oculta en `.env`. Si ya instalaste el proyecto, ejecuta `python setup_config.py --edit` para cambiar credenciales. `python run.py` también abrirá el asistente automáticamente si falta la configuración básica.

## Configuración

La configuración se realiza automáticamente con el asistente. También puedes editar `.env` manualmente:

```env
TELEGRAM_BOT_TOKEN=PEGA_TOKEN_NUEVO
ADMIN_CHAT_ID=TU_CHAT_ID
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
GROQ_ENABLED=true

MARKET_PROVIDER=yfinance
DEFAULT_TIMEFRAME=5m
SCAN_INTERVAL_SECONDS=180
SCAN_MIN_CONFIDENCE=68
SCAN_COOLDOWN_SECONDS=900
AUTO_SCAN_ENABLED=false
MULTI_TIMEFRAME_CONFIRMATION=true
TIMEZONE=America/Guatemala
```

No subas `.env`, `data/`, ni `logs/` a GitHub. El archivo `.env.example` no contiene secretos.

**Seguridad:** si el token de Telegram se publicó en logs, revócalo en @BotFather y crea uno nuevo. Nunca pegues tokens en issues, capturas ni commits.

## Comandos Telegram

- `/start` — ayuda.
- `/status` — estado y configuración no sensible.
- `/analizar EUR/USD 5m` — análisis de un activo.
- `/scan` — escaneo inmediato de todos los activos configurados.
- `/auto_on` — activar escaneo automático.
- `/auto_off` — detener escaneo automático.
- `/activos` — activos admitidos.
- `/timeframes` — temporalidades admitidas.
- `/senales` — últimas señales guardadas.
- `/stats` — estadísticas globales.
- `/stats_hoy` — estadísticas del día local.
- `/riesgo` — explicación de gestión de riesgo.
- `/calcriesgo 1000 1 1.0850 1.0800` — calcula exposición teórica.
- `/patrones EUR/USD 5m` — patrones en la última vela.
- `/backtest EUR/USD 5m 1000` — simulación histórica.
- `/health` — diagnóstico de Telegram y Groq.
- `/exportar` — exportar historial CSV.
- `/modelos` — consultar modelos Groq disponibles (si está configurado).

Para analizar un activo se aceptan alias (`EUR/USD`, `BTC/USD`, `XAU/USD`) o ticker Yahoo incluido en la lista blanca.

## Estrategia y límites

El motor combina puntuaciones técnicas; los porcentajes mostrados son **índices heurísticos de confluencia, no probabilidades de ganar**. Una señal requiere consenso mínimo y filtros de calidad. Los niveles ATR son referencias educativas, no órdenes ni recomendaciones.

Las velas más recientes pueden estar incompletas. Los intervalos intradía de Yahoo tienen límites de historial y disponibilidad. El bot marca la hora de la última vela y evita afirmar que una cotización es "tiempo real".

El resultado WIN/LOSS se introduce manualmente. Para una evaluación real se necesita un sistema de resolución por precio y vencimiento, incluyendo spread, comisiones y deslizamiento. Las estadísticas manuales no son backtesting.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

Las pruebas unitarias no requieren credenciales ni conexión a mercado. La prueba de importación completa se omite automáticamente si aún no están instaladas las dependencias de `requirements.txt`.

## Documentación adicional

- `docs/ARQUITECTURA.md` — módulos y flujo de datos.
- `docs/ESTRATEGIA_Y_VALIDACION.md` — indicadores, backtesting y protocolo de validación.
- `docs/TERMUX.md` — instalación y mantenimiento en Android.
- `CHANGELOG.md` — cambios de la versión.

## Estructura

```text
trading-ai-analyzer-pro/
├── trading_bot/
│   ├── config.py
│   ├── indicators.py
│   ├── market.py
│   ├── strategies.py
│   ├── patterns.py
│   ├── risk.py
│   ├── backtest.py
│   ├── diagnostics.py
│   ├── ai.py
│   ├── storage.py
│   ├── analyzer.py
│   ├── scanner.py
│   ├── formatting.py
│   └── handlers.py
├── tests/
├── docs/
├── data/
├── logs/
├── .env.example
├── .gitignore
├── install.sh
├── run.py
├── setup_config.py
└── requirements.txt
```

## Aviso

Software informativo y educativo. No ofrece asesoramiento financiero, no garantiza resultados y no ejecuta operaciones. Verifica datos y realiza pruebas históricas/forward-test antes de tomar decisiones.
