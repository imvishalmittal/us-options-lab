"""Causal, order-free SPY entry research used by the QuantConnect wrapper.

The simulator deliberately operates on the underlying rather than options.  Its
job is to reject weak entry families before option contract selection and exit
overlays (including US V2/V3) are evaluated.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, time
from math import inf
from statistics import median
from typing import Any, Optional


REGULAR_OPEN = time(9, 30)
OPENING_RANGE_END = time(9, 45)
FORCED_EXIT = time(15, 45)


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self) -> None:
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise ValueError("prices must be positive")
        if self.high < max(self.open, self.close) or self.low > min(self.open, self.close):
            raise ValueError("invalid OHLC bar")
        if self.volume < 0:
            raise ValueError("volume cannot be negative")


@dataclass(frozen=True)
class Signal:
    strategy: str
    direction: int
    observed_at: datetime
    stop: float
    reason: str


@dataclass
class Trade:
    strategy: str
    direction: int
    signal_at: datetime
    opened_at: datetime
    entry: float
    stop: float
    target: float
    risk: float
    max_favorable_r: float = 0.0
    max_adverse_r: float = 0.0
    closed_at: Optional[datetime] = None
    exit: Optional[float] = None
    exit_reason: Optional[str] = None
    result_r: Optional[float] = None


@dataclass(frozen=True)
class Rejection:
    direction: int
    timestamp: datetime
    high: float
    low: float


class StrategyRunner:
    """One independent strategy simulation with at most one trade per day."""

    def __init__(self, strategy: str) -> None:
        if strategy not in {"US_OPENING_DRIVE", "US_FAILED_OPEN_BREAK"}:
            raise ValueError(f"unsupported strategy: {strategy}")
        self.strategy = strategy
        self.completed: list[Trade] = []
        self.events: list[dict[str, Any]] = []
        self.sessions: set[date] = set()
        self.traded_sessions: set[date] = set()
        self._session_date: Optional[date] = None
        self._opening_high: Optional[float] = None
        self._opening_low: Optional[float] = None
        self._opening_open: Optional[float] = None
        self._opening_bars = 0
        self._cum_price_volume = 0.0
        self._cum_volume = 0.0
        self._recent_volumes: list[float] = []
        self._drive_direction = 0
        self._drive_count = 0
        self._rejection: Optional[Rejection] = None
        self._pending: Optional[Signal] = None
        self._trade: Optional[Trade] = None
        self._traded_today = False

    @property
    def opening_range_complete(self) -> bool:
        return self._opening_bars >= 15

    @property
    def pending_signal(self) -> Optional[Signal]:
        return self._pending

    @property
    def open_trade(self) -> Optional[Trade]:
        return self._trade

    def on_bar(self, bar: Bar) -> list[dict[str, Any]]:
        """Consume one completed regular-session bar in chronological order."""
        clock = bar.timestamp.time()
        if clock < REGULAR_OPEN or clock >= time(16, 0):
            return []

        if self._session_date != bar.timestamp.date():
            self._reset_session(bar.timestamp.date())

        new_events: list[dict[str, Any]] = []
        self._enter_pending_at_next_open(bar, new_events)
        if self._trade is not None:
            self._manage_trade(bar, new_events)

        prior_volumes = self._recent_volumes[-10:]
        self._update_session_indicators(bar)

        if clock < OPENING_RANGE_END:
            self._update_opening_range(bar)
        elif (
            self.opening_range_complete
            and self._trade is None
            and self._pending is None
            and not self._traded_today
        ):
            signal = self._detect_signal(bar, prior_volumes)
            if signal is not None:
                self._pending = signal
                new_events.append(self._event("SIGNAL", bar.timestamp, reason=signal.reason))

        self._recent_volumes.append(bar.volume)
        self.events.extend(new_events)
        return new_events

    def _reset_session(self, session_date: date) -> None:
        if self._trade is not None:
            raise RuntimeError("an overnight trade would violate the research protocol")
        self._session_date = session_date
        self.sessions.add(session_date)
        self._opening_high = None
        self._opening_low = None
        self._opening_open = None
        self._opening_bars = 0
        self._cum_price_volume = 0.0
        self._cum_volume = 0.0
        self._recent_volumes = []
        self._drive_direction = 0
        self._drive_count = 0
        self._rejection = None
        self._pending = None
        self._traded_today = False

    def _update_opening_range(self, bar: Bar) -> None:
        if self._opening_open is None:
            self._opening_open = bar.open
        self._opening_high = bar.high if self._opening_high is None else max(self._opening_high, bar.high)
        self._opening_low = bar.low if self._opening_low is None else min(self._opening_low, bar.low)
        self._opening_bars += 1

    def _update_session_indicators(self, bar: Bar) -> None:
        typical = (bar.high + bar.low + bar.close) / 3.0
        self._cum_price_volume += typical * bar.volume
        self._cum_volume += bar.volume

    @property
    def _vwap(self) -> float:
        if self._cum_volume <= 0:
            return 0.0
        return self._cum_price_volume / self._cum_volume

    def _detect_signal(self, bar: Bar, prior_volumes: list[float]) -> Optional[Signal]:
        if self.strategy == "US_OPENING_DRIVE":
            return self._opening_drive_signal(bar, prior_volumes)
        return self._failed_break_signal(bar)

    def _range_is_eligible(self) -> bool:
        assert self._opening_open is not None
        assert self._opening_high is not None
        assert self._opening_low is not None
        width_fraction = (self._opening_high - self._opening_low) / self._opening_open
        return 0.0015 <= width_fraction <= 0.0080

    def _opening_drive_signal(self, bar: Bar, prior_volumes: list[float]) -> Optional[Signal]:
        clock = bar.timestamp.time()
        if clock < time(9, 45) or clock > time(10, 30) or not self._range_is_eligible():
            return None
        assert self._opening_high is not None and self._opening_low is not None
        threshold = 0.0005
        direction = 0
        if bar.close >= self._opening_high * (1 + threshold) and bar.close > self._vwap:
            direction = 1
        elif bar.close <= self._opening_low * (1 - threshold) and bar.close < self._vwap:
            direction = -1

        if direction == 0:
            self._drive_direction = 0
            self._drive_count = 0
            return None
        if direction == self._drive_direction:
            self._drive_count += 1
        else:
            self._drive_direction = direction
            self._drive_count = 1

        volume_ok = len(prior_volumes) >= 10 and bar.volume >= 1.25 * median(prior_volumes)
        if self._drive_count < 2 or not volume_ok:
            return None

        width = self._opening_high - self._opening_low
        stop = (
            self._opening_high - 0.25 * width
            if direction == 1
            else self._opening_low + 0.25 * width
        )
        return Signal(
            strategy=self.strategy,
            direction=direction,
            observed_at=bar.timestamp,
            stop=stop,
            reason="two_close_opening_range_acceptance_with_vwap_and_volume",
        )

    def _failed_break_signal(self, bar: Bar) -> Optional[Signal]:
        clock = bar.timestamp.time()
        if clock < time(9, 45) or clock > time(11, 0) or not self._range_is_eligible():
            return None
        assert self._opening_high is not None and self._opening_low is not None

        if self._rejection is not None:
            rejection = self._rejection
            self._rejection = None
            confirmed = (
                rejection.direction == 1
                and bar.close > rejection.high
                and bar.close > self._vwap
            ) or (
                rejection.direction == -1
                and bar.close < rejection.low
                and bar.close < self._vwap
            )
            if confirmed:
                stop = rejection.low if rejection.direction == 1 else rejection.high
                return Signal(
                    strategy=self.strategy,
                    direction=rejection.direction,
                    observed_at=bar.timestamp,
                    stop=stop,
                    reason="opening_range_sweep_rejection_then_next_bar_confirmation",
                )

        sweep = 0.0005
        if (
            bar.low <= self._opening_low * (1 - sweep)
            and bar.close > self._opening_low
            and bar.close > self._vwap
        ):
            self._rejection = Rejection(1, bar.timestamp, bar.high, bar.low)
        elif (
            bar.high >= self._opening_high * (1 + sweep)
            and bar.close < self._opening_high
            and bar.close < self._vwap
        ):
            self._rejection = Rejection(-1, bar.timestamp, bar.high, bar.low)
        return None

    def _enter_pending_at_next_open(self, bar: Bar, new_events: list[dict[str, Any]]) -> None:
        signal = self._pending
        if signal is None or bar.timestamp <= signal.observed_at:
            return
        self._pending = None
        risk = (bar.open - signal.stop) * signal.direction
        if risk <= 0:
            new_events.append(self._event("REJECTED", bar.timestamp, reason="gap_invalidated_stop"))
            return
        target = bar.open + signal.direction * 2.0 * risk
        self._trade = Trade(
            strategy=self.strategy,
            direction=signal.direction,
            signal_at=signal.observed_at,
            opened_at=bar.timestamp,
            entry=bar.open,
            stop=signal.stop,
            target=target,
            risk=risk,
        )
        self._traded_today = True
        assert self._session_date is not None
        self.traded_sessions.add(self._session_date)
        new_events.append(self._event("ENTRY", bar.timestamp, price=bar.open))

    def _manage_trade(self, bar: Bar, new_events: list[dict[str, Any]]) -> None:
        trade = self._trade
        assert trade is not None
        favorable = (bar.high - trade.entry) if trade.direction == 1 else (trade.entry - bar.low)
        adverse = (trade.entry - bar.low) if trade.direction == 1 else (bar.high - trade.entry)
        trade.max_favorable_r = max(trade.max_favorable_r, favorable / trade.risk)
        trade.max_adverse_r = max(trade.max_adverse_r, adverse / trade.risk)

        if trade.direction == 1:
            gap_stop = bar.open <= trade.stop
            stop_hit = bar.low <= trade.stop
            target_hit = bar.high >= trade.target
        else:
            gap_stop = bar.open >= trade.stop
            stop_hit = bar.high >= trade.stop
            target_hit = bar.low <= trade.target

        # Stop-first is deliberately adverse when minute-bar ordering is unknown.
        if gap_stop:
            self._close_trade(bar, bar.open, "STOP_GAP", new_events)
        elif stop_hit:
            self._close_trade(bar, trade.stop, "STOP", new_events)
        elif target_hit:
            self._close_trade(bar, trade.target, "TARGET_2R", new_events)
        elif bar.timestamp.time() >= FORCED_EXIT:
            self._close_trade(bar, bar.close, "FORCED_1545", new_events)

    def _close_trade(
        self, bar: Bar, exit_price: float, reason: str, new_events: list[dict[str, Any]]
    ) -> None:
        trade = self._trade
        assert trade is not None
        trade.closed_at = bar.timestamp
        trade.exit = exit_price
        trade.exit_reason = reason
        trade.result_r = (exit_price - trade.entry) * trade.direction / trade.risk
        self.completed.append(trade)
        self._trade = None
        new_events.append(self._event("EXIT", bar.timestamp, price=exit_price, reason=reason))

    def _event(self, kind: str, timestamp: datetime, **details: Any) -> dict[str, Any]:
        return {"strategy": self.strategy, "event": kind, "timestamp": timestamp.isoformat(), **details}

    def summary(self) -> dict[str, Any]:
        results = [trade.result_r for trade in self.completed if trade.result_r is not None]
        wins = [value for value in results if value > 0]
        losses = [value for value in results if value < 0]
        gross_win = sum(wins)
        gross_loss = -sum(losses)
        equity = 0.0
        peak = 0.0
        max_drawdown = 0.0
        losing_streak = 0
        max_losing_streak = 0
        for value in results:
            equity += value
            peak = max(peak, equity)
            max_drawdown = max(max_drawdown, peak - equity)
            losing_streak = losing_streak + 1 if value < 0 else 0
            max_losing_streak = max(max_losing_streak, losing_streak)
        profit_factor: Optional[float]
        if gross_loss > 0:
            profit_factor = gross_win / gross_loss
        elif gross_win > 0:
            profit_factor = inf
        else:
            profit_factor = None
        return {
            "strategy": self.strategy,
            "sessions": len(self.sessions),
            "trades": len(results),
            "noTradeSessions": len(self.sessions - self.traded_sessions),
            "winRate": (len(wins) / len(results)) if results else None,
            "averageR": (sum(results) / len(results)) if results else None,
            "totalR": sum(results),
            "profitFactor": profit_factor,
            "maxDrawdownR": max_drawdown,
            "longestLosingStreak": max_losing_streak,
            "tradesDetail": [asdict(trade) for trade in self.completed],
        }


class EntryResearchEngine:
    """Run the two frozen V1 entry hypotheses independently."""

    def __init__(self) -> None:
        self.runners = {
            name: StrategyRunner(name)
            for name in ("US_OPENING_DRIVE", "US_FAILED_OPEN_BREAK")
        }

    def on_bar(self, bar: Bar) -> list[dict[str, Any]]:
        events: list[dict[str, Any]] = []
        for runner in self.runners.values():
            events.extend(runner.on_bar(bar))
        return events

    def summaries(self) -> dict[str, dict[str, Any]]:
        return {name: runner.summary() for name, runner in self.runners.items()}
