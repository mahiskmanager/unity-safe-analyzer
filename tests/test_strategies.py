import unittest
from trading_bot.strategies import evaluate

def sample(**updates):
    base = {
        "ema9": 110, "ema21": 105, "ema50": 100, "ema200": 95,
        "price": 111, "macd": 2, "macd_signal": 1, "macd_hist": 1,
        "rsi": 60, "cci": 100, "roc": 1, "stoch_k": 0.7,
        "stoch_d": 0.5, "candle_bull": True, "candle_bear": False,
        "body_ratio": 0.7, "adx": 30, "atr": 1,
        "bb_width": 3, "stale": False
    }
    base.update(updates)
    return base

class StrategyTests(unittest.TestCase):
    def test_bullish_candidate(self):
        result = evaluate(sample())
        self.assertEqual(result["direction"], "CALL")
        self.assertGreaterEqual(result["confidence"], 50)

    def test_stale_data_never_signal(self):
        result = evaluate(sample(stale=True))
        self.assertEqual(result["direction"], "NO_OPERAR")

    def test_zero_atr_never_signal(self):
        result = evaluate(sample(atr=0))
        self.assertEqual(result["direction"], "NO_OPERAR")

    def test_conflicting_or_weak_data_filtered(self):
        result = evaluate(sample(
            ema9=99, ema21=101, ema50=100, ema200=100,
            macd=0, macd_signal=1, macd_hist=-1,
            rsi=50, cci=0, roc=0, stoch_k=0.5,
            stoch_d=0.5, candle_bull=False, candle_bear=False,
            body_ratio=0.1, adx=10
        ))
        self.assertEqual(result["direction"], "NO_OPERAR")

if __name__ == "__main__":
    unittest.main()
