"""QuantConnect Cloud wrapper for the order-free SPY entry study.

Copy this file and ``strategy_core.py`` into one QuantConnect Python project.
The algorithm records virtual trades only; it never calls a LEAN order method.
"""

from AlgorithmImports import *
import json
import math

from strategy_core import Bar as ResearchBar
from strategy_core import EntryResearchEngine


PERIODS = {
    "development": ((2018, 1, 1), (2022, 12, 31)),
    "validation": ((2023, 1, 1), (2024, 12, 31)),
}


class UsOptionsEntryResearchAlgorithm(QCAlgorithm):
    def initialize(self):
        period = (self.get_parameter("period") or "development").strip().lower()
        if period not in PERIODS:
            raise ValueError("period must be development or validation; 2025+ is reserved holdout")
        start, end = PERIODS[period]
        self.set_start_date(*start)
        self.set_end_date(*end)
        self.set_cash(1000)
        self.set_time_zone("America/New_York")
        self.spy = self.add_equity("SPY", Resolution.MINUTE, extended_market_hours=False).symbol
        self.engine = EntryResearchEngine()
        self.period_name = period

    def on_data(self, data):
        bar = data.bars.get(self.spy)
        if bar is None:
            return
        research_bar = ResearchBar(
            timestamp=bar.time,
            open=float(bar.open),
            high=float(bar.high),
            low=float(bar.low),
            close=float(bar.close),
            volume=float(bar.volume),
        )
        self.engine.on_bar(research_bar)

    def on_end_of_algorithm(self):
        for strategy, summary in self.engine.summaries().items():
            compact = {key: value for key, value in summary.items() if key != "tradesDetail"}
            if math.isinf(compact.get("profitFactor") or 0):
                compact["profitFactor"] = "Infinity"
            self.log(json.dumps({"period": self.period_name, **compact}, sort_keys=True))
