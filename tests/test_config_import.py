import importlib.util
import unittest

REQUIRED = ('ta', 'yfinance', 'telegram', 'dotenv')
HAS_DEPS = all(importlib.util.find_spec(name) is not None for name in REQUIRED)

@unittest.skipUnless(HAS_DEPS, 'Instala requirements.txt para ejecutar la prueba de importación completa.')
class ImportTests(unittest.TestCase):
    def test_modules_import(self):
        import trading_bot.config
        import trading_bot.indicators
        import trading_bot.market
        import trading_bot.strategies
        import trading_bot.storage
        import trading_bot.analyzer
        import trading_bot.handlers
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
