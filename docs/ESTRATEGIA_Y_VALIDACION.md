# Motor técnico y validación

## Indicadores incluidos
- Tendencia: EMA 9, 21, 50, 100 y 200.
- Momentum: RSI, MACD, ROC, CCI y Stochastic RSI.
- Volatilidad: ATR y Bandas de Bollinger.
- Fuerza: ADX.
- Flujo: MFI y OBV.
- Estructura: soporte/resistencia recientes y canales Donchian.
- Velas: doji, martillo/rechazo inferior, estrella fugaz/rechazo superior, envolventes e inside bar.

## Confianza
El valor en pantalla es un índice heurístico de confluencia, no una probabilidad calibrada de ganar. Un valor 80/100 no significa 80% de probabilidad.

## Backtesting
`/backtest ACTIVO TEMPORALIDAD [capital]` ejecuta una estrategia didáctica:
- Calcula señal al cierre de una vela y entra en la apertura de la siguiente.
- Usa stop y objetivo definidos por múltiplos de ATR.
- Si stop y objetivo aparecen dentro del mismo rango OHLC, contabiliza primero el stop.
- Descuenta comisión y deslizamiento simulados.
- Reporta P/L, win rate, profit factor y drawdown máximo.

No incluye spread real, swaps, financiación, liquidez, gaps completos ni reglas específicas de contratos. Yahoo Finance limita el historial intradía; una muestra corta no demuestra robustez.

## Protocolo recomendado
1. Ejecutar backtests en varios activos y temporalidades.
2. Separar datos de desarrollo y datos fuera de muestra.
3. Ajustar parámetros solo con el tramo de desarrollo.
4. Repetir en datos no usados durante el ajuste.
5. Realizar forward-test en demo durante varias semanas.
6. Registrar señales y comparar resultados netos de costos.
7. No aumentar riesgo por una racha ganadora ni aplicar martingala.
