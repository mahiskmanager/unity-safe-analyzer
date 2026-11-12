import unittest
import pandas as pd
from trading_bot.backtest import run_backtest

class BacktestTests(unittest.TestCase):
    def test_requires_history(self):
        with self.assertRaises(ValueError):
            run_backtest(pd.DataFrame())

if __name__ == '__main__':
    unittest.main()

class BacktestExecutionTests(unittest.TestCase):
    def test_enters_next_bar_and_closes_at_end(self):
        n = 120
        frame = pd.DataFrame({
            'Open': [100.0] * n, 'High': [100.2] * n,
            'Low': [99.8] * n, 'Close': [100.1] * n,
            'EMA9': [102.0] * n, 'EMA21': [101.0] * n,
            'EMA50': [100.0] * n, 'RSI': [60.0] * n,
            'MACD': [2.0] * n, 'MACD_SIGNAL': [1.0] * n,
            'ADX': [30.0] * n, 'ATR': [1.0] * n,
        })
        result = run_backtest(frame, 1000)
        self.assertEqual(result['trades'], 1)
        self.assertEqual(result['trades_detail'][0]['reason'], 'END_OF_DATA')
