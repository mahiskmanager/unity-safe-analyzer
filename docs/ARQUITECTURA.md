# Arquitectura del sistema

## Flujo de análisis
1. El handler valida que el mensaje proceda del chat privado administrador.
2. `market.py` descarga OHLCV desde Yahoo Finance, aplica reintentos y caché en memoria.
3. `indicators.py` calcula EMA, RSI, MACD, Bollinger, ATR, ADX, CCI, Stochastic RSI, ROC, MFI, OBV, Williams %R y canales Donchian.
4. `strategies.py` evalúa confluencias de tendencia, momentum, fuerza y flujo.
5. `analyzer.py` puede exigir confirmación de una temporalidad superior.
6. `ai.py` solicita a Groq una explicación limitada; la IA no decide la dirección.
7. `storage.py` guarda señales y resultados manuales en SQLite con WAL.
8. `scanner.py` permite escaneo manual o periódico con enfriamiento de alertas.

## Separación de responsabilidades
- `patterns.py`: patrones de velas con reglas explícitas.
- `risk.py`: cálculo matemático de exposición y relación riesgo/beneficio.
- `backtest.py`: simulación OHLC sin look-ahead, con costos y regla conservadora si stop y objetivo aparecen en la misma vela.
- `diagnostics.py`: estado de Telegram y Groq sin revelar secretos.

## Seguridad
- `.env` no debe versionarse.
- Los secretos se solicitan con entrada oculta y permisos privados cuando el sistema lo permite.
- El bot acepta mensajes únicamente desde el chat privado configurado.
- Los mensajes de estado no muestran tokens ni API keys.
- No conecta con exchanges ni brokers y no ejecuta órdenes.

## Límites de datos
Yahoo Finance puede retrasar cotizaciones, restringir intervalos intradía o devolver huecos. Una vela abierta puede cambiar. Los resultados del backtest dependen de la calidad de OHLC y del modelo de costos.
