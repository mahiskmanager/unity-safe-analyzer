import unittest
import pandas as pd
from trading_bot.patterns import detect_patterns

class PatternTests(unittest.TestCase):
    def test_doji(self):
        frame = pd.DataFrame([
            {'Open': 10, 'High': 11, 'Low': 9, 'Close': 10},
            {'Open': 10, 'High': 11, 'Low': 9, 'Close': 10},
            {'Open': 10, 'High': 11, 'Low': 9, 'Close': 10.01},
        ])
        names = [x['name'] for x in detect_patterns(frame)]
        self.assertIn('Doji', names)

if __name__ == '__main__':
    unittest.main()
