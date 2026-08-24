"""Causal, order-free SPY entry research for the second US hypothesis cycle.

The runners in this module simulate the underlying only. They deliberately do
not select option contracts or place broker orders. A strategy must first show
an underlying edge before it can consume the more expensive option replay.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from math import inf
from statistics import mean
from typing import Any, Optional

try:
    from .strategy_core import ResearchBar
except ImportError:  # QuantConnect stores project files as top-level modules.
    from strategy_core import ResearchBar


REGULAR_OPEN = time(9, 30)
REGULAR_CLOSE = time(16, 0)
NOISE_CHECKPOINTS = {
    time(10, 0), time(10, 30), time(11, 0), time(11, 30),
    time(12, 0), time(12, 30), time(13, 0), time(13, 30),
    time(14, 0), time(14, 30), time(15, 0),
}


@dataclass(frozen=True)
class V2Signal:
    strategy: str
    direction: int
    observed_at: datetime
    stop: float
    reason: str


@dataclass
class V2Trade:
    strategy: str
    direction: int
    signal_at: datetime
    opened_at: datetime
    entry: float
    stop: float
    risk: float
    max_favorable_r: float = 0.0
    max_adverse_r: float = 0.0
    closed_at: Optional[datetime] = None
    exit: Optional[float] = None
    exit_reason: Optional[str] = None
    result_r: Optional[float] = None


class _SingleTradeRunner:
    """Shared causal execution for one virtual trade per session."""

    def __init__(self, strategy: str) -> None:
        self.strategy = strategy
        self.completed: list[V2Trade] = []
        self.events: list[dict[str, Any]] = []
        self.sessions: set[date] = set()
        self.traded_sessions: set[date] = set()
        self._session_date: Optional[date] = None
        self._pending: Optional[V2Signal] = None
        self._trade: Optional[V2Trade] = None
        self._traded_today = False

    @property
    def pending_signal(self) -> Optional[V2Signal]:
        return self._pending

    @property
    def open_trade(self) -> Optional[V2Trade]:
        return self._trade

    def _enter_pending(self, bar: ResearchBar, events: list[dict[str, Any]]) -> None:
        signal = self._pending
        if signal is None or bar.timestamp <= signal.observed_at:
            return
        self._pending = None
        risk = (bar.open - signal.stop) * signal.direction
        if risk <= 0:
            events.append(self._event("REJECTED", bar.timestamp, reason="gap_invalidated_stop"))
            return
        self._trade = V2Trade(
            strategy=self.strategy,
            direction=signal.direction,
            signal_at=signal.observed_at,
            opened_at=bar.timestamp,
            entry=bar.open,
            stop=signal.stop,
            risk=risk,
        )
        self._traded_today = True
        assert self._session_date is not None
        self.traded_sessions.add(self._session_date)
        events.append(self._event("ENTRY", bar.timestamp, price=bar.open,
                                  direction=signal.direction, stop=signal.stop))

    def _manage_stop(self, bar: ResearchBar, events: list[dict[str, Any]]) -> None:
        trade = self._trade
        if trade is None:
            return
        favorable = bar.high - trade.entry if trade.direction == 1 else trade.entry - bar.low
        adverse = trade.entry - bar.low if trade.direction == 1 else bar.high - trade.entry
        trade.max_favorable_r = max(trade.max_favorable_r, favorable / trade.risk)
        trade.max_adverse_r = max(trade.max_adverse_r, adverse / trade.risk)
        gap = bar.open <= trade.stop if trade.direction == 1 else bar.open >= trade.stop
        hit = bar.low <= trade.stop if trade.direction == 1 else bar.high >= trade.stop
        if gap:
            self._close(bar, bar.open, "STOP_GAP", events)
        elif hit:
            self._close(bar, trade.stop, "STOP", events)

    def _close(self, bar: ResearchBar, exit_price: float, reason: str,
               events: list[dict[str, Any]]) -> None:
        trade = self._trade
        assert trade is not None
        trade.closed_at = bar.timestamp
        trade.exit = exit_price
        trade.exit_reason = reason
        trade.result_r = (exit_price - trade.entry) * trade.direction / trade.risk
        self.completed.append(trade)
        self._trade = None
        events.append(self._event("EXIT", bar.timestamp, price=exit_price, reason=reason))

    def force_close(self, bar: ResearchBar, reason: str) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        if self._trade is not None:
            self._close(bar, bar.close, reason, events)
        self._pending = None
        self.events.extend(events)
        return events

    def summary(self) -> dict[str, Any]:
        results = [trade.result_r for trade in self.completed if trade.result_r is not None]
        wins = [value for value in results if value > 0]
        losses = [value for value in results if value < 0]
        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0
        for value in results:
            equity += value
            peak = max(peak, equity)
            max_drawdown = max(max_drawdown, peak - equity)
        gross_profit = sum(wins)
        gross_loss = -sum(losses)
        return {
            "strategy": self.strategy,
            "sessions": len(self.sessions),
            "tradedSessions": len(self.traded_sessions),
            "trades": len(results),
            "winRate": len(wins) / len(results) if results else 0.0,
            "averageR": mean(results) if results else 0.0,
            "totalR": sum(results),
            "profitFactor": gross_profit / gross_loss if gross_loss else (inf if gross_profit else 0.0),
            "maxDrawdownR": max_drawdown,
            "tradesDetail": [asdict(trade) for trade in self.completed],
        }

    def _event(self, event: str, timestamp: datetime, **payload: Any) -> dict[str, Any]:
        return {"event": event, "strategy": self.strategy, "timestamp": timestamp, **payload}


class NoiseAreaMomentumRunner(_SingleTradeRunner):
    """Gap-adjusted 14-session, minute-of-day noise-band momentum."""

    def __init__(self) -> None:
        super().__init__("US_NOISE_AREA_MOMENTUM")
        self._profiles: dict[int, list[float]] = {}
        self._current_profile: dict[int, float] = {}
        self._session_open: Optional[float] = None
        self._previous_close: Optional[float] = None
        self._last_close: Optional[float] = None
        self._cum_price_volume = 0.0
        self._cum_volume = 0.0

    @property
    def vwap(self) -> float:
        return self._cum_price_volume / self._cum_volume if self._cum_volume > 0 else 0.0

    def on_bar(self, bar: ResearchBar) -> list[dict[str, Any]]:
        clock = bar.timestamp.time()
        if clock < REGULAR_OPEN or clock >= REGULAR_CLOSE:
            return []
        if self._session_date != bar.timestamp.date():
            self._roll_session(bar)

        events: list[dict[str, Any]] = []
        self._enter_pending(bar, events)
        self._manage_stop(bar, events)

        typical = (bar.high + bar.low + bar.close) / 3.0
        self._cum_price_volume += typical * bar.volume
        self._cum_volume += bar.volume
        assert self._session_open is not None
        minute_index = (clock.hour * 60 + clock.minute) - (9 * 60 + 30)
        self._current_profile[minute_index] = abs(bar.close / self._session_open - 1.0)

        if (self._trade is None and self._pending is None and not self._traded_today
                and clock in NOISE_CHECKPOINTS):
            signal = self._detect_signal(bar, minute_index)
            if signal is not None:
                self._pending = signal
                events.append(self._event("SIGNAL", bar.timestamp,
                                          direction=signal.direction,
                                          stop=signal.stop,
                                          reason=signal.reason))

        # The completed bar's VWAP is effective only for the next bar.
        if self._trade is not None:
            if self._trade.direction == 1:
                self._trade.stop = max(self._trade.stop, self.vwap)
            else:
                self._trade.stop = min(self._trade.stop, self.vwap)

        self._last_close = bar.close
        self.events.extend(events)
        return events

    def _roll_session(self, first_bar: ResearchBar) -> None:
        if self._trade is not None:
            raise RuntimeError("an overnight trade would violate the research protocol")
        if self._session_date is not None:
            for minute_index, move in self._current_profile.items():
                history = self._profiles.setdefault(minute_index, [])
                history.append(move)
                del history[:-14]
            self._previous_close = self._last_close
        self._session_date = first_bar.timestamp.date()
        self.sessions.add(self._session_date)
        self._pending = None
        self._traded_today = False
        self._current_profile = {}
        self._session_open = first_bar.open
        self._cum_price_volume = 0.0
        self._cum_volume = 0.0

    def _detect_signal(self, bar: ResearchBar, minute_index: int) -> Optional[V2Signal]:
        history = self._profiles.get(minute_index, [])
        if len(history) < 14 or self._previous_close is None or self.vwap <= 0:
            return None
        expected_move = mean(history)
        assert self._session_open is not None
        upper = max(self._session_open, self._previous_close) * (1.0 + expected_move)
        lower = min(self._session_open, self._previous_close) * (1.0 - expected_move)
        if bar.close > upper and bar.close > self.vwap:
            direction = 1
        elif bar.close < lower and bar.close < self.vwap:
            direction = -1
        else:
            return None
        return V2Signal(self.strategy, direction, bar.timestamp, self.vwap,
                        "gap_adjusted_14_session_noise_break_with_vwap")


class ClosingHalfHourMomentumRunner(_SingleTradeRunner):
    """First and penultimate half-hour agreement predicting the close."""

    def __init__(self) -> None:
        super().__init__("US_CLOSING_HALF_HOUR_MOMENTUM")
        self._previous_close: Optional[float] = None
        self._last_close: Optional[float] = None
        self._first_half_return: Optional[float] = None
        self._penultimate_start: Optional[float] = None

    def on_bar(self, bar: ResearchBar) -> list[dict[str, Any]]:
        clock = bar.timestamp.time()
        if clock < REGULAR_OPEN or clock >= REGULAR_CLOSE:
            return []
        if self._session_date != bar.timestamp.date():
            self._roll_session(bar.timestamp.date())

        events: list[dict[str, Any]] = []
        self._enter_pending(bar, events)
        self._manage_stop(bar, events)

        if clock == time(9, 59) and self._previous_close is not None:
            self._first_half_return = bar.close / self._previous_close - 1.0
        if clock == time(14, 59):
            self._penultimate_start = bar.close
        if (clock == time(15, 29) and not self._traded_today and self._trade is None
                and self._pending is None and self._first_half_return is not None
                and self._penultimate_start is not None):
            penultimate_return = bar.close / self._penultimate_start - 1.0
            if self._first_half_return == 0 or penultimate_return == 0:
                self._last_close = bar.close
                self.events.extend(events)
                return events
            first_direction = 1 if self._first_half_return > 0 else -1
            second_direction = 1 if penultimate_return > 0 else -1
            if first_direction == second_direction:
                direction = first_direction
                stop = bar.close * (1.0 - direction * 0.003)
                self._pending = V2Signal(
                    self.strategy, direction, bar.timestamp, stop,
                    "first_and_penultimate_half_hour_direction_agree",
                )
                events.append(self._event("SIGNAL", bar.timestamp,
                                          direction=direction, stop=stop,
                                          reason=self._pending.reason))

        if clock >= time(15, 55) and self._trade is not None:
            self._close(bar, bar.close, "FORCED_1555", events)

        self._last_close = bar.close
        self.events.extend(events)
        return events

    def _roll_session(self, session_date: date) -> None:
        if self._trade is not None:
            raise RuntimeError("an overnight trade would violate the research protocol")
        if self._session_date is not None:
            self._previous_close = self._last_close
        self._session_date = session_date
        self.sessions.add(session_date)
        self._pending = None
        self._traded_today = False
        self._first_half_return = None
        self._penultimate_start = None


class IntradayV2ResearchEngine:
    """Runs the two predeclared V2 hypotheses as alternative simulations."""

    def __init__(self) -> None:
        self.runners = {
            "US_NOISE_AREA_MOMENTUM": NoiseAreaMomentumRunner(),
            "US_CLOSING_HALF_HOUR_MOMENTUM": ClosingHalfHourMomentumRunner(),
        }

    def on_bar(self, bar: ResearchBar) -> dict[str, list[dict[str, Any]]]:
        return {name: runner.on_bar(bar) for name, runner in self.runners.items()}

    def force_close(self, bar: ResearchBar, reason: str) -> None:
        for runner in self.runners.values():
            runner.force_close(bar, reason)

    def summaries(self) -> dict[str, dict[str, Any]]:
        return {name: runner.summary() for name, runner in self.runners.items()}
