import unittest
from trading_bot.risk import position_size, risk_reward

class RiskTests(unittest.TestCase):
    def test_position_size(self):
        result = position_size(1000, 1, 100, 95)
        self.assertAlmostEqual(result['risk_cash'], 10)
        self.assertAlmostEqual(result['units'], 2)
    def test_risk_limit(self):
        with self.assertRaises(ValueError):
            position_size(1000, 10, 100, 95)
    def test_zero_stop_distance(self):
        with self.assertRaises(ValueError):
            position_size(1000, 1, 100, 100)
    def test_rr(self):
        self.assertAlmostEqual(risk_reward(100, 95, 110), 2)

if __name__ == '__main__':
    unittest.main()
