from datetime import datetime, timedelta
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from quantconnect.strategy_core import Bar, StrategyRunner


DAY = datetime(2024, 1, 3, 9, 30)


def bar(minute, open_, high, low, close, volume=100):
    return Bar(DAY + timedelta(minutes=minute), open_, high, low, close, volume)


def seed_opening_range(runner):
    for minute in range(15):
        runner.on_bar(bar(minute, 100.0, 100.20, 99.80, 100.0, 100))


class QuantConnectStrategyCoreTests(unittest.TestCase):
    def test_opening_range_requires_fifteen_completed_bars(self):
        runner = StrategyRunner("US_OPENING_DRIVE")
        for minute in range(14):
            runner.on_bar(bar(minute, 100, 100.2, 99.8, 100))
        self.assertFalse(runner.opening_range_complete)
        runner.on_bar(bar(14, 100, 100.2, 99.8, 100))
        self.assertTrue(runner.opening_range_complete)

    def test_opening_drive_requires_two_accepted_closes_and_enters_next_bar(self):
        runner = StrategyRunner("US_OPENING_DRIVE")
        seed_opening_range(runner)
        # Supply ten causal, prior volume observations before confirmation.
        for minute in range(15, 25):
            runner.on_bar(bar(minute, 100.0, 100.15, 99.95, 100.05, 100))
        runner.on_bar(bar(25, 100.20, 100.35, 100.15, 100.30, 100))
        self.assertIsNone(runner.pending_signal)
        runner.on_bar(bar(26, 100.30, 100.45, 100.25, 100.40, 150))
        self.assertIsNotNone(runner.pending_signal)
        self.assertIsNone(runner.open_trade)
        runner.on_bar(bar(27, 100.44, 100.50, 100.35, 100.46, 100))
        self.assertEqual(runner.open_trade.entry, 100.44)
        self.assertEqual(runner.open_trade.opened_at, DAY + timedelta(minutes=27))

    def test_failed_break_requires_rejection_then_confirmation_then_next_open(self):
        runner = StrategyRunner("US_FAILED_OPEN_BREAK")
        seed_opening_range(runner)
        rejection = bar(15, 99.90, 100.08, 99.70, 100.02, 130)
        runner.on_bar(rejection)
        self.assertIsNone(runner.pending_signal)
        confirmation = bar(16, 100.02, 100.18, 100.00, 100.12, 120)
        runner.on_bar(confirmation)
        self.assertIsNotNone(runner.pending_signal)
        self.assertIsNone(runner.open_trade)
        runner.on_bar(bar(17, 100.14, 100.20, 100.10, 100.18, 100))
        self.assertEqual(runner.open_trade.entry, 100.14)
        self.assertEqual(runner.open_trade.stop, 99.70)

    def test_same_bar_stop_and_target_uses_stop_first(self):
        runner = StrategyRunner("US_FAILED_OPEN_BREAK")
        seed_opening_range(runner)
        runner.on_bar(bar(15, 99.90, 100.08, 99.70, 100.02))
        runner.on_bar(bar(16, 100.02, 100.18, 100.00, 100.12))
        runner.on_bar(bar(17, 100.14, 100.20, 100.10, 100.18))
        trade = runner.open_trade
        self.assertIsNotNone(trade)
        runner.on_bar(bar(18, 100.14, trade.target + 0.01, trade.stop - 0.01, 100.15))
        self.assertEqual(runner.completed[0].exit_reason, "STOP")
        self.assertAlmostEqual(runner.completed[0].result_r, -1.0)

    def test_forced_exit_at_1545(self):
        runner = StrategyRunner("US_FAILED_OPEN_BREAK")
        seed_opening_range(runner)
        runner.on_bar(bar(15, 99.90, 100.08, 99.70, 100.02))
        runner.on_bar(bar(16, 100.02, 100.18, 100.00, 100.12))
        runner.on_bar(bar(17, 100.14, 100.20, 100.10, 100.18))
        late_minute = (15 * 60 + 45) - (9 * 60 + 30)
        runner.on_bar(bar(late_minute, 100.20, 100.25, 100.15, 100.22))
        self.assertEqual(runner.completed[0].exit_reason, "FORCED_1545")
        self.assertIsNone(runner.open_trade)

    def test_never_opens_second_trade_same_day(self):
        runner = StrategyRunner("US_FAILED_OPEN_BREAK")
        seed_opening_range(runner)
        runner.on_bar(bar(15, 99.90, 100.08, 99.70, 100.02))
        runner.on_bar(bar(16, 100.02, 100.18, 100.00, 100.12))
        runner.on_bar(bar(17, 100.14, 100.20, 100.10, 100.18))
        stop = runner.open_trade.stop
        runner.on_bar(bar(18, 100.10, 100.15, stop - 0.01, stop, 100))
        runner.on_bar(bar(19, 99.90, 100.08, 99.70, 100.02, 130))
        runner.on_bar(bar(20, 100.02, 100.18, 100.00, 100.12, 130))
        runner.on_bar(bar(21, 100.14, 100.20, 100.10, 100.18, 130))
        self.assertEqual(len(runner.completed), 1)
        self.assertIsNone(runner.open_trade)

    def test_gap_through_stop_exits_at_worse_open(self):
        runner = StrategyRunner("US_FAILED_OPEN_BREAK")
        seed_opening_range(runner)
        runner.on_bar(bar(15, 99.90, 100.08, 99.70, 100.02))
        runner.on_bar(bar(16, 100.02, 100.18, 100.00, 100.12))
        runner.on_bar(bar(17, 100.14, 100.20, 100.10, 100.18))
        runner.on_bar(bar(18, 99.60, 99.70, 99.50, 99.65))
        self.assertEqual(runner.completed[0].exit_reason, "STOP_GAP")
        self.assertLess(runner.completed[0].result_r, -1.0)


if __name__ == "__main__":
    unittest.main()
