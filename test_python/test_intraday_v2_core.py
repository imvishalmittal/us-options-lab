from datetime import datetime, timedelta
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from quantconnect.intraday_v2_core import ClosingHalfHourMomentumRunner, NoiseAreaMomentumRunner
from quantconnect.strategy_core import ResearchBar


def make_bar(day, minute, open_, high, low, close, volume=100):
    stamp = datetime(2024, 1, day, 9, 30) + timedelta(minutes=minute)
    return ResearchBar(stamp, open_, high, low, close, volume)


class IntradayV2CoreTests(unittest.TestCase):
    def _seed_noise_history(self, runner):
        for day in range(1, 16):
            runner.on_bar(make_bar(day, 0, 100, 100.1, 99.9, 100.0))
            runner.on_bar(make_bar(day, 30, 100, 100.25, 99.9, 100.20))

    def test_noise_area_requires_fourteen_completed_prior_sessions(self):
        runner = NoiseAreaMomentumRunner()
        for day in range(1, 15):
            runner.on_bar(make_bar(day, 0, 100, 100.1, 99.9, 100.0))
            runner.on_bar(make_bar(day, 30, 100, 100.25, 99.9, 100.20))
        runner.on_bar(make_bar(15, 0, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(15, 30, 100.3, 100.5, 100.2, 100.4))
        self.assertIsNone(runner.pending_signal)

    def test_noise_signal_enters_next_bar_and_vwap_trail_is_causal(self):
        runner = NoiseAreaMomentumRunner()
        self._seed_noise_history(runner)
        runner.on_bar(make_bar(16, 0, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(16, 30, 100.3, 100.6, 100.2, 100.5))
        self.assertIsNotNone(runner.pending_signal)
        self.assertIsNone(runner.open_trade)
        signal_stop = runner.pending_signal.stop
        runner.on_bar(make_bar(16, 31, 100.52, 100.70, 100.45, 100.65))
        self.assertIsNotNone(runner.open_trade)
        self.assertEqual(runner.open_trade.opened_at.minute, 1)
        self.assertGreaterEqual(runner.open_trade.stop, signal_stop)

    def test_noise_stop_first_uses_gap_open(self):
        runner = NoiseAreaMomentumRunner()
        self._seed_noise_history(runner)
        runner.on_bar(make_bar(16, 0, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(16, 30, 100.3, 100.6, 100.2, 100.5))
        runner.on_bar(make_bar(16, 31, 100.52, 100.70, 100.45, 100.65))
        stop = runner.open_trade.stop
        runner.on_bar(make_bar(16, 32, stop - 0.10, stop - 0.05, stop - 0.20, stop - 0.10))
        self.assertEqual(runner.completed[0].exit_reason, "STOP_GAP")
        self.assertAlmostEqual(runner.completed[0].exit, stop - 0.10)

    def _seed_closing_signal(self, runner):
        runner.on_bar(make_bar(1, 0, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(1, 389, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(2, 0, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(2, 29, 100.2, 100.3, 100.1, 100.25))
        runner.on_bar(make_bar(2, 329, 100.3, 100.4, 100.2, 100.30))
        runner.on_bar(make_bar(2, 359, 100.5, 100.6, 100.4, 100.55))

    def test_closing_momentum_requires_direction_agreement_and_next_open(self):
        runner = ClosingHalfHourMomentumRunner()
        self._seed_closing_signal(runner)
        self.assertIsNotNone(runner.pending_signal)
        self.assertIsNone(runner.open_trade)
        runner.on_bar(make_bar(2, 360, 100.56, 100.65, 100.50, 100.60))
        self.assertIsNotNone(runner.open_trade)
        self.assertEqual(runner.open_trade.direction, 1)

    def test_closing_momentum_exits_at_1555(self):
        runner = ClosingHalfHourMomentumRunner()
        self._seed_closing_signal(runner)
        runner.on_bar(make_bar(2, 360, 100.56, 100.65, 100.50, 100.60))
        runner.on_bar(make_bar(2, 385, 100.75, 100.80, 100.70, 100.76))
        self.assertEqual(runner.completed[0].exit_reason, "FORCED_1555")

    def test_closing_momentum_does_not_infer_direction_from_zero_return(self):
        runner = ClosingHalfHourMomentumRunner()
        runner.on_bar(make_bar(1, 0, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(1, 389, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(2, 0, 100, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(2, 29, 100.0, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(2, 329, 100.0, 100.1, 99.9, 100.0))
        runner.on_bar(make_bar(2, 359, 100.2, 100.3, 100.1, 100.25))
        self.assertIsNone(runner.pending_signal)


if __name__ == "__main__":
    unittest.main()
