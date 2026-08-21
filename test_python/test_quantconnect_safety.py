import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]


class QuantConnectSafetyTests(unittest.TestCase):
    def test_cloud_wrapper_contains_no_order_calls(self):
        source = (ROOT / "quantconnect" / "main.py").read_text(encoding="utf-8").lower()
        forbidden = (
            "market_order(",
            "limit_order(",
            "stop_market_order(",
            "set_holdings(",
            "liquidate(",
            "exercise_option(",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_holdout_dates_are_not_runnable(self):
        source = (ROOT / "quantconnect" / "main.py").read_text(encoding="utf-8")
        self.assertIn('"development": ((2018, 1, 1), (2022, 12, 31))', source)
        self.assertIn('"validation": ((2023, 1, 1), (2024, 12, 31))', source)
        self.assertNotIn("2025,", source)
        self.assertNotIn("2026,", source)


if __name__ == "__main__":
    unittest.main()
