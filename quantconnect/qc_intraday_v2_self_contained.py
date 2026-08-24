from AlgorithmImports import *
from collections import defaultdict, deque
import json


class UsIntradayV2Research(QCAlgorithm):
    CHECKPOINTS = {(h, m) for h in range(10, 16) for m in (0, 30) if not (h == 15 and m == 30)}

    def initialize(self):
        self.set_start_date(2018, 1, 1)
        self.set_end_date(2018, 12, 31)
        self.set_cash(1000)
        self.set_time_zone("America/New_York")
        self.spy = self.add_equity("SPY", Resolution.MINUTE, extended_market_hours=False).symbol
        self.current_day = None
        self.last_bar = None
        self.sessions = 0
        self.traded_days = {"noise": set(), "close": set()}
        self.pending = {"noise": None, "close": None}
        self.trade = {"noise": None, "close": None}
        self.results = {"noise": [], "close": []}
        self.profiles = defaultdict(lambda: deque(maxlen=14))
        self.current_profile = {}
        self.previous_close = None
        self.last_close = None
        self.schedule.on(self.date_rules.every_day(self.spy),
                         self.time_rules.before_market_close(self.spy, 1), self.force_exit)

    def reset_day(self, bar):
        if self.current_day is not None:
            for minute, move in self.current_profile.items():
                self.profiles[minute].append(move)
            self.previous_close = self.last_close
        self.current_day = bar.time.date()
        self.sessions += 1
        self.current_profile = {}
        self.session_open = float(bar.open)
        self.pv = self.volume = 0.0
        self.first_half = self.penultimate_start = None
        self.pending = {"noise": None, "close": None}

    def on_data(self, data):
        bar = data.bars.get(self.spy)
        if bar is None:
            return
        if self.current_day != bar.time.date():
            self.reset_day(bar)
        self.last_bar = bar
        for name in ("noise", "close"):
            self.enter_pending(name, bar)
            self.manage_stop(name, bar)

        typical = (float(bar.high) + float(bar.low) + float(bar.close)) / 3.0
        self.pv += typical * float(bar.volume)
        self.volume += float(bar.volume)
        vwap = self.pv / self.volume if self.volume else 0.0
        clock = (bar.time.hour, bar.time.minute)
        minute = bar.time.hour * 60 + bar.time.minute - 570
        self.current_profile[minute] = abs(float(bar.close) / self.session_open - 1.0)

        if clock in self.CHECKPOINTS and not self.trade["noise"] and not self.pending["noise"] \
                and self.current_day not in self.traded_days["noise"]:
            history = self.profiles[minute]
            if len(history) == 14 and self.previous_close is not None and vwap:
                expected = sum(history) / 14.0
                upper = max(self.session_open, self.previous_close) * (1.0 + expected)
                lower = min(self.session_open, self.previous_close) * (1.0 - expected)
                close = float(bar.close)
                direction = 1 if close > upper and close > vwap else (-1 if close < lower and close < vwap else 0)
                if direction:
                    self.pending["noise"] = (direction, bar.time, vwap)

        if self.trade["noise"]:
            t = self.trade["noise"]
            t["stop"] = max(t["stop"], vwap) if t["direction"] == 1 else min(t["stop"], vwap)

        if clock == (9, 59) and self.previous_close is not None:
            self.first_half = float(bar.close) / self.previous_close - 1.0
        if clock == (14, 59):
            self.penultimate_start = float(bar.close)
        if clock == (15, 29) and self.current_day not in self.traded_days["close"] \
                and not self.trade["close"] and not self.pending["close"] \
                and self.first_half is not None and self.penultimate_start is not None:
            later = float(bar.close) / self.penultimate_start - 1.0
            if self.first_half * later > 0:
                direction = 1 if self.first_half > 0 else -1
                stop = float(bar.close) * (1.0 - direction * 0.003)
                self.pending["close"] = (direction, bar.time, stop)
        if clock >= (15, 55) and self.trade["close"]:
            self.close_trade("close", float(bar.close), "FORCED_1555")

        self.last_close = float(bar.close)

    def enter_pending(self, name, bar):
        signal = self.pending[name]
        if signal is None or bar.time <= signal[1]:
            return
        self.pending[name] = None
        direction, _, stop = signal
        entry = float(bar.open)
        risk = (entry - stop) * direction
        if risk <= 0:
            return
        self.trade[name] = {"direction": direction, "entry": entry, "stop": stop, "risk": risk}
        self.traded_days[name].add(self.current_day)

    def manage_stop(self, name, bar):
        t = self.trade[name]
        if not t:
            return
        direction, stop = t["direction"], t["stop"]
        gap = float(bar.open) <= stop if direction == 1 else float(bar.open) >= stop
        hit = float(bar.low) <= stop if direction == 1 else float(bar.high) >= stop
        if gap:
            self.close_trade(name, float(bar.open), "STOP_GAP")
        elif hit:
            self.close_trade(name, stop, "STOP")

    def close_trade(self, name, price, reason):
        t = self.trade[name]
        if not t:
            return
        result = (price - t["entry"]) * t["direction"] / t["risk"]
        self.results[name].append(result)
        self.trade[name] = None

    def force_exit(self):
        if self.last_bar is None or self.last_bar.time.date() != self.time.date():
            return
        for name in ("noise", "close"):
            if self.trade[name]:
                self.close_trade(name, float(self.last_bar.close), "SESSION_EXIT")
            self.pending[name] = None

    def on_end_of_algorithm(self):
        labels = {"noise": "US_NOISE_AREA_MOMENTUM", "close": "US_CLOSING_HALF_HOUR_MOMENTUM"}
        for name, values in self.results.items():
            wins = [x for x in values if x > 0]
            losses = [x for x in values if x < 0]
            equity = peak = drawdown = 0.0
            for value in values:
                equity += value
                peak = max(peak, equity)
                drawdown = max(drawdown, peak - equity)
            payload = {"period": "development_2018", "strategy": labels[name],
                       "sessions": self.sessions, "trades": len(values),
                       "winRate": len(wins) / len(values) if values else 0.0,
                       "averageR": sum(values) / len(values) if values else 0.0,
                       "totalR": sum(values),
                       "profitFactor": sum(wins) / -sum(losses) if losses else ("Infinity" if wins else 0.0),
                       "maxDrawdownR": drawdown}
            self.log(json.dumps(payload, sort_keys=True))
