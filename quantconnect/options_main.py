"""QuantConnect wrapper for order-free SPY option replay.

Copy as ``main.py`` beside ``strategy_core.py`` and ``option_replay_core.py``.
No LEAN order API is called; all fills update alternative virtual ledgers.
"""

from AlgorithmImports import *
from datetime import datetime
import json
import math

from option_replay_core import (
    OptionCandidate,
    OptionQuoteBar,
    OptionReplayEngine,
    select_contract,
)
from strategy_core import ResearchBar, StrategyRunner


PERIODS = {
    "feasibility": ((2024, 1, 2), (2024, 2, 2)),
    "development_2018": ((2018, 1, 1), (2018, 12, 31)),
    "development_2019": ((2019, 1, 1), (2019, 12, 31)),
    "development_2020": ((2020, 1, 1), (2020, 12, 31)),
    "development_2021": ((2021, 1, 1), (2021, 12, 31)),
    "development_2022": ((2022, 1, 1), (2022, 12, 31)),
    "validation_2023": ((2023, 1, 1), (2023, 12, 31)),
    "validation_2024": ((2024, 1, 1), (2024, 12, 31)),
    "development": ((2018, 1, 1), (2022, 12, 31)),
    "validation": ((2023, 1, 1), (2024, 12, 31)),
}

DEFAULT_PERIOD = "feasibility"
DEFAULT_SELECTOR = "delta"


class UsOptionsReplayAlgorithm(QCAlgorithm):
    def initialize(self):
        period = (self.get_parameter("period") or DEFAULT_PERIOD).strip().lower()
        selector = (self.get_parameter("selector") or DEFAULT_SELECTOR).strip().lower()
        if period not in PERIODS:
            raise ValueError(f"unknown period: {period}")
        if selector not in {"delta", "premium", "us_balanced"}:
            raise ValueError("selector must be delta, premium, or us_balanced")
        start, end = PERIODS[period]
        self.set_start_date(*start)
        self.set_end_date(*end)
        self.set_cash(1000)
        self.set_time_zone("America/New_York")
        self.spy = self.add_equity(
            "SPY", Resolution.MINUTE, data_normalization_mode=DataNormalizationMode.RAW
        ).symbol
        option = self.add_option("SPY", Resolution.MINUTE)
        if selector == "us_balanced":
            option.set_filter(
                lambda universe: universe.include_weeklys().strikes(-10, 10).expiration(5, 10)
            )
        else:
            option.set_filter(
                lambda universe: universe.include_weeklys().strikes(-6, 6).expiration(1, 7)
            )
        self.option_symbol = option.symbol
        self.entry = StrategyRunner("US_OPENING_DRIVE")
        self.replay = OptionReplayEngine(selector)
        self.period_name = period
        self.selector_name = selector
        self.pending = None
        self.pending_structural_exit_reason = None
        self.last_option_quote = None
        self.last_research_bar = None
        self.schedule.on(
            self.date_rules.every_day(self.spy),
            self.time_rules.before_market_close(self.spy, 15),
            self._force_session_exit,
        )

    def on_data(self, data):
        spy_bar = data.bars.get(self.spy)
        if spy_bar is None:
            return
        research_bar = ResearchBar(
            timestamp=spy_bar.time,
            open=float(spy_bar.open),
            high=float(spy_bar.high),
            low=float(spy_bar.low),
            close=float(spy_bar.close),
            volume=float(spy_bar.volume),
        )
        self.last_research_bar = research_bar
        open_quote = self._quote_for_open_contract(data)
        if open_quote is not None:
            self.last_option_quote = open_quote
            self.replay.process_quote(open_quote)
            if self.pending_structural_exit_reason is not None:
                self.replay.structural_exit(
                    open_quote, self.pending_structural_exit_reason
                )
                self.pending_structural_exit_reason = None

        events = self.entry.on_bar(research_bar)
        for event in events:
            if event["event"] == "SIGNAL":
                self._select_at_signal(data, event)
            elif event["event"] == "REJECTED":
                self.pending = None
                self.replay.reject("UNDERLYING_ENTRY_REJECTED")
            elif event["event"] == "ENTRY":
                self._enter_at_next_quote(data)
            elif event["event"] == "EXIT":
                if not self.replay.structural_open:
                    continue
                quote = self._quote_for_open_contract(data)
                if quote is not None:
                    self.last_option_quote = quote
                    self.replay.structural_exit(
                        quote, f"UNDERLYING_{event.get('reason', 'EXIT')}"
                    )
                    self.pending_structural_exit_reason = None
                else:
                    self.pending_structural_exit_reason = (
                        f"UNDERLYING_{event.get('reason', 'EXIT')}_NEXT_QUOTE"
                    )
                    self.replay.reject("STRUCTURAL_EXIT_DEFERRED_MISSING_QUOTE")

    def _select_at_signal(self, data, event):
        chain = data.option_chains.get(self.option_symbol)
        if chain is None:
            self.pending = None
            self.replay.reject("SIGNAL_CHAIN_MISSING")
            return
        candidates = []
        for contract in chain:
            expiry = (
                contract.expiry.date()
                if hasattr(contract.expiry, "date")
                else contract.expiry
            )
            right = "CALL" if contract.right == OptionRight.CALL else "PUT"
            delta = float(contract.greeks.delta)
            candidates.append(
                OptionCandidate(
                    symbol=contract.symbol,
                    expiry=expiry,
                    right=right,
                    strike=float(contract.strike),
                    delta=delta,
                    bid=float(contract.bid_price),
                    ask=float(contract.ask_price),
                )
            )
        selected = select_contract(
            candidates,
            int(event["direction"]),
            self.time.date(),
            self.selector_name,
        )
        if selected is None:
            self.pending = None
            self.replay.reject("NO_ELIGIBLE_SIGNAL_TIME_CONTRACT")
            return
        self.pending = {
            "candidate": selected,
            "signal_at": datetime.fromisoformat(event["timestamp"]),
            "direction": int(event["direction"]),
        }

    def _enter_at_next_quote(self, data):
        pending = self.pending
        self.pending = None
        if pending is None:
            return
        quote = self._quote(data, pending["candidate"].symbol)
        if quote is None:
            self.replay.reject("ENTRY_QUOTE_MISSING")
            return
        if self.replay.enter(
            pending["candidate"], pending["signal_at"], pending["direction"], quote
        ):
            self.last_option_quote = quote
            self.replay.process_quote(quote)

    def _quote_for_open_contract(self, data):
        symbol_text = self.replay.open_symbol
        if symbol_text is None:
            return None
        for symbol, quote_bar in data.quote_bars.items():
            if str(symbol) == symbol_text:
                return quote_snapshot(quote_bar)
        return None

    def _quote(self, data, symbol):
        quote_bar = data.quote_bars.get(symbol)
        return None if quote_bar is None else quote_snapshot(quote_bar)

    def _force_session_exit(self):
        if self.last_research_bar is not None:
            self.entry.force_close(
                self.last_research_bar,
                "FORCED_15_MIN_BEFORE_EXCHANGE_CLOSE",
            )
        if self.last_option_quote is not None:
            self.replay.force_exit(self.last_option_quote)
        self.pending_structural_exit_reason = None

    def on_end_of_algorithm(self):
        entry_summary = self.entry.summary()
        entry_summary.pop("tradesDetail", None)
        self.log(json.dumps({"period": self.period_name, **entry_summary}, sort_keys=True))
        for summary in self.replay.summaries().values():
            compact = {
                key: value for key, value in summary.items() if key != "tradesDetail"
            }
            if math.isinf(compact.get("profitFactor") or 0):
                compact["profitFactor"] = "Infinity"
            self.log(
                json.dumps(
                    {
                        "period": self.period_name,
                        "cohortsEntered": self.replay.cohorts_entered,
                        "rejections": self.replay.rejections,
                        **compact,
                    },
                    sort_keys=True,
                )
            )


def quote_snapshot(bar):
    if bar.bid is None or bar.ask is None:
        return None
    return OptionQuoteBar(
        timestamp=bar.time,
        bid_open=float(bar.bid.open),
        bid_high=float(bar.bid.high),
        bid_low=float(bar.bid.low),
        bid_close=float(bar.bid.close),
        ask_open=float(bar.ask.open),
        ask_high=float(bar.ask.high),
        ask_low=float(bar.ask.low),
        ask_close=float(bar.ask.close),
    )
