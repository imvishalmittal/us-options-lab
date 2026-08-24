import pathlib
import unittest


ROOT = pathlib.Path(__file__).parents[1]


class QuantConnectSafetyTests(unittest.TestCase):
    def test_cloud_wrapper_contains_no_order_calls(self):
        forbidden = (
            "market_order(",
            "limit_order(",
            "stop_market_order(",
            "set_holdings(",
            "liquidate(",
            "exercise_option(",
        )
        for filename in ("main.py", "options_main.py", "intraday_v2_main.py"):
            source = (ROOT / "quantconnect" / filename).read_text(encoding="utf-8").lower()
            for token in forbidden:
                self.assertNotIn(token, source)

    def test_options_wrapper_closes_underlying_state_on_exchange_schedule(self):
        source = (ROOT / "quantconnect" / "options_main.py").read_text(encoding="utf-8")
        self.assertIn("self.last_research_bar = research_bar", source)
        self.assertIn("self.entry.force_close(", source)
        self.assertIn("FORCED_15_MIN_BEFORE_EXCHANGE_CLOSE", source)

    def test_holdout_dates_are_not_runnable(self):
        source = (ROOT / "quantconnect" / "main.py").read_text(encoding="utf-8")
        self.assertIn('"development": ((2018, 1, 1), (2022, 12, 31))', source)
        self.assertIn('"validation": ((2023, 1, 1), (2024, 12, 31))', source)
        self.assertNotIn("2025,", source)
        self.assertNotIn("2026,", source)

    def test_intraday_v2_preserves_holdout_and_exchange_exit(self):
        source = (ROOT / "quantconnect" / "intraday_v2_main.py").read_text(
            encoding="utf-8"
        )
        periods = source.split("PERIODS =", 1)[1].split("class ", 1)[0]
        self.assertNotIn("2025", periods)
        self.assertNotIn("2026", periods)
        self.assertIn("2025+ remains reserved holdout", source)
        self.assertIn("before_market_close(self.spy, 1)", source)


if __name__ == "__main__":
    unittest.main()
