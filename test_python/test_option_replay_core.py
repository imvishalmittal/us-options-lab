from datetime import datetime, timedelta
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from quantconnect.option_replay_core import (
    OptionCandidate,
    OptionQuoteBar,
    OptionReplayEngine,
    select_contract,
)


NOW = datetime(2024, 1, 3, 10, 0)


def candidate(symbol, right="CALL", delta=0.40, bid=1.75, ask=1.80, dte=2, strike=470):
    return OptionCandidate(
        symbol, NOW.date() + timedelta(days=dte), right, strike, delta, bid, ask
    )


def quote(minute, bid_open, bid_high, bid_low, bid_close, ask_open=None):
    ask_open = ask_open if ask_open is not None else bid_open + 0.05
    return OptionQuoteBar(
        NOW + timedelta(minutes=minute),
        bid_open,
        bid_high,
        bid_low,
        bid_close,
        ask_open,
        max(ask_open, bid_high + 0.05),
        min(ask_open, bid_low + 0.05),
        bid_close + 0.05,
    )


class OptionReplayTests(unittest.TestCase):
    def test_delta_selector_uses_nearest_expiry_and_closest_to_point_four(self):
        choices = [
            candidate("far", delta=0.40, dte=3),
            candidate("near-38", delta=0.38, dte=2),
            candidate("near-41", delta=0.41, dte=2),
        ]
        self.assertEqual(
            select_contract(choices, 1, NOW.date(), "delta").symbol, "near-41"
        )

    def test_selector_rejects_zero_dte_wrong_right_and_wide_quotes(self):
        choices = [
            candidate("zero", dte=0),
            candidate("put", right="PUT"),
            candidate("wide", bid=1.40, ask=1.80),
        ]
        self.assertIsNone(select_contract(choices, 1, NOW.date(), "delta"))

    def test_premium_selector_targets_one_eighty(self):
        choices = [candidate("a", ask=1.70), candidate("b", ask=1.81)]
        self.assertEqual(
            select_contract(choices, 1, NOW.date(), "premium").symbol, "b"
        )

    def test_us_balanced_selector_prefers_seven_dte_and_point_three_delta(self):
        choices = [
            candidate("six-day", delta=0.30, dte=6),
            candidate("seven-24", delta=0.24, dte=7),
            candidate("seven-31", delta=0.31, dte=7),
            candidate("too-near", delta=0.30, dte=4),
        ]
        self.assertEqual(
            select_contract(choices, 1, NOW.date(), "us_balanced").symbol,
            "seven-31",
        )

    def test_all_variants_share_one_contract_and_entry_fill(self):
        engine = OptionReplayEngine("delta")
        selected = candidate("SPY-C")
        entry_quote = quote(1, 1.76, 1.84, 1.75, 1.80, ask_open=1.80)
        self.assertTrue(engine.enter(selected, NOW, 1, entry_quote))
        entries = {book.open_trade.entry_fill for book in engine.books.values()}
        symbols = {book.open_trade.symbol for book in engine.books.values()}
        self.assertEqual(entries, {1.81})
        self.assertEqual(symbols, {"SPY-C"})

    def test_v2_activation_is_effective_on_next_bar(self):
        engine = OptionReplayEngine("delta")
        engine.enter(
            candidate("SPY-C"), NOW, 1, quote(1, 1.76, 1.84, 1.75, 1.80, 1.80)
        )
        engine.process_quote(quote(2, 1.82, 2.21, 1.80, 2.20))
        v2 = engine.books["US_V2_LITERAL"].open_trade
        self.assertEqual(v2.active_stop, 2.01)
        engine.process_quote(quote(3, 2.08, 2.10, 2.00, 2.02))
        closed = engine.books["US_V2_LITERAL"].completed[0]
        self.assertEqual(closed.exit_reason, "TRAIL_STOP")
        self.assertEqual(closed.exit_fill, 2.00)

    def test_v3_five_cent_ratchets_before_ten_cent(self):
        engine = OptionReplayEngine("delta")
        engine.enter(
            candidate("SPY-C"), NOW, 1, quote(1, 1.76, 1.84, 1.75, 1.80, 1.80)
        )
        engine.process_quote(quote(2, 1.82, 1.87, 1.80, 1.86))
        self.assertEqual(
            engine.books["US_V3_005_LITERAL"].open_trade.active_stop, 1.66
        )
        self.assertEqual(
            engine.books["US_V3_010_LITERAL"].open_trade.active_stop, 1.60
        )

    def test_us_fixed_percent_exit_uses_entry_scaled_stop_and_two_r_target(self):
        engine = OptionReplayEngine("us_balanced")
        engine.enter(
            candidate("SPY-C", dte=7), NOW, 1, quote(1, 1.76, 1.84, 1.75, 1.80, 1.80)
        )
        trade = engine.books["US_FIXED_2R_25PCT"].open_trade
        self.assertEqual(1.36, trade.active_stop)
        self.assertEqual(2.71, trade.active_target)
        engine.process_quote(quote(2, 1.80, 2.75, 1.70, 2.70))
        closed = engine.books["US_FIXED_2R_25PCT"].completed[0]
        self.assertEqual("TARGET_2R", closed.exit_reason)
        self.assertEqual(2.70, closed.exit_fill)

    def test_us_percent_trail_activates_on_next_bar(self):
        engine = OptionReplayEngine("us_balanced")
        engine.enter(
            candidate("SPY-C", dte=7), NOW, 1, quote(1, 1.76, 1.84, 1.75, 1.80, 1.80)
        )
        engine.process_quote(quote(2, 1.80, 2.36, 1.70, 2.30))
        trade = engine.books["US_TRAIL_30_15PCT"].open_trade
        self.assertEqual(2.01, trade.active_stop)
        engine.process_quote(quote(3, 2.10, 2.15, 2.00, 2.05))
        closed = engine.books["US_TRAIL_30_15PCT"].completed[0]
        self.assertEqual("TRAIL_STOP", closed.exit_reason)
        self.assertEqual(2.00, closed.exit_fill)

    def test_stop_gap_uses_worse_bid_open_and_exit_slippage(self):
        engine = OptionReplayEngine("delta")
        engine.enter(
            candidate("SPY-C"), NOW, 1, quote(1, 1.76, 1.84, 1.75, 1.80, 1.80)
        )
        engine.process_quote(quote(2, 1.50, 1.55, 1.45, 1.52))
        closed = engine.books["US_V2_LITERAL"].completed[0]
        self.assertEqual(closed.exit_fill, 1.49)
        self.assertEqual(closed.exit_reason, "INITIAL_STOP")

    def test_structural_exit_does_not_close_v2_and_v3(self):
        engine = OptionReplayEngine("delta")
        engine.enter(
            candidate("SPY-C"), NOW, 1, quote(1, 1.76, 1.84, 1.75, 1.80, 1.80)
        )
        engine.structural_exit(
            quote(2, 1.90, 1.95, 1.85, 1.92), "UNDERLYING_TARGET_2R"
        )
        self.assertIsNone(engine.books["STRUCTURAL_2R"].open_trade)
        self.assertIsNotNone(engine.books["US_V2_LITERAL"].open_trade)

    def test_session_exit_closes_all_alternative_books(self):
        engine = OptionReplayEngine("delta")
        engine.enter(
            candidate("SPY-C"), NOW, 1, quote(1, 1.76, 1.84, 1.75, 1.80, 1.80)
        )
        engine.force_exit(quote(20, 1.90, 1.95, 1.85, 1.92))
        self.assertTrue(all(book.open_trade is None for book in engine.books.values()))
        self.assertTrue(
            all(book.completed[0].exit_reason == "SESSION_EXIT" for book in engine.books.values())
        )
        structural = engine.summaries()["STRUCTURAL_2R"]
        self.assertEqual(structural["winningNetPnlUsd"], structural["netPnlUsd"])
        self.assertEqual(0, structural["losingNetPnlUsd"])
        self.assertGreater(structural["peakEquityUsd"], 1000)
        self.assertEqual(1000, structural["minimumEquityUsd"])
        self.assertFalse(structural["capitalBelowMaximumDebit"])
        self.assertFalse(structural["capitalExhausted"])

    def test_entry_above_debit_limit_rejects_entire_cohort(self):
        engine = OptionReplayEngine("delta")
        accepted = engine.enter(
            candidate("SPY-C", ask=2.19),
            NOW,
            1,
            quote(1, 2.10, 2.20, 2.05, 2.15, 2.20),
        )
        self.assertFalse(accepted)
        self.assertTrue(all(book.open_trade is None for book in engine.books.values()))


if __name__ == "__main__":
    unittest.main()
