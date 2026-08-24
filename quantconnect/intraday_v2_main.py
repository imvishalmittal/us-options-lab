"""QuantConnect wrapper for the order-free SPY Intraday V2 entry study.

Copy this file as ``main.py`` together with ``strategy_core.py`` and
``intraday_v2_core.py`` into a separate QuantConnect project. It records only
virtual underlying trades and contains no order calls.
"""

from AlgorithmImports import *
import json
import math

from strategy_core import ResearchBar
from intraday_v2_core import IntradayV2ResearchEngine


PERIODS = {
    "development_2018": ((2018, 1, 1), (2018, 12, 31)),
    "development_2019": ((2019, 1, 1), (2019, 12, 31)),
    "development_2020": ((2020, 1, 1), (2020, 12, 31)),
    "development_2021": ((2021, 1, 1), (2021, 12, 31)),
    "development_2022": ((2022, 1, 1), (2022, 12, 31)),
    "development": ((2018, 1, 1), (2022, 12, 31)),
    "validation_2023": ((2023, 1, 1), (2023, 12, 31)),
    "validation_2024_clean": ((2024, 2, 1), (2024, 12, 31)),
}


class UsOptionsIntradayV2ResearchAlgorithm(QCAlgorithm):
    def initialize(self):
        period = (self.get_parameter("period") or "development_2018").strip().lower()
        if period not in PERIODS:
            raise ValueError("unsupported period; 2025+ remains reserved holdout")
        start, end = PERIODS[period]
        self.set_start_date(*start)
        self.set_end_date(*end)
        self.set_cash(1000)
        self.set_time_zone("America/New_York")
        self.spy = self.add_equity("SPY", Resolution.MINUTE, extended_market_hours=False).symbol
        self.engine = IntradayV2ResearchEngine()
        self.period_name = period
        self.last_research_bar = None
        self.schedule.on(
            self.date_rules.every_day(self.spy),
            self.time_rules.before_market_close(self.spy, 1),
            self._force_session_exit,
        )

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
        self.last_research_bar = research_bar
        self.engine.on_bar(research_bar)

    def _force_session_exit(self):
        bar = self.last_research_bar
        if bar is None or bar.timestamp.date() != self.time.date():
            return
        self.engine.force_close(bar, "FORCED_1_MIN_BEFORE_EXCHANGE_CLOSE")

    def on_end_of_algorithm(self):
        for strategy, summary in self.engine.summaries().items():
            compact = {key: value for key, value in summary.items() if key != "tradesDetail"}
            if math.isinf(compact.get("profitFactor") or 0):
                compact["profitFactor"] = "Infinity"
            self.log(json.dumps({"period": self.period_name, **compact}, sort_keys=True))
