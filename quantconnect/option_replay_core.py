"""Provider-neutral, order-free replay for long SPY option variants."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
from math import inf
from typing import Any, Optional


STARTING_CASH_USD = 1000.0
MAXIMUM_DEBIT_USD = 220.0
CONTRACT_MULTIPLIER = 100
COMMISSION_PER_SIDE_USD = 0.65
SLIPPAGE_PER_CONTRACT_USD = 0.01
MINIMUM_PREMIUM_USD = 1.60
MAXIMUM_PREMIUM_USD = 2.20
MAXIMUM_SPREAD_USD = 0.20
MAXIMUM_SPREAD_FRACTION = 0.15


@dataclass(frozen=True)
class OptionCandidate:
    symbol: Any
    expiry: date
    right: str
    strike: float
    delta: Optional[float]
    bid: float
    ask: float


@dataclass(frozen=True)
class OptionQuoteBar:
    timestamp: datetime
    bid_open: float
    bid_high: float
    bid_low: float
    bid_close: float
    ask_open: float
    ask_high: float
    ask_low: float
    ask_close: float

    def __post_init__(self) -> None:
        values = (
            self.bid_open,
            self.bid_high,
            self.bid_low,
            self.bid_close,
            self.ask_open,
            self.ask_high,
            self.ask_low,
            self.ask_close,
        )
        if min(values) <= 0:
            raise ValueError("option bid/ask OHLC must be positive")
        if self.bid_high < max(self.bid_open, self.bid_close) or self.bid_low > min(
            self.bid_open, self.bid_close
        ):
            raise ValueError("invalid bid OHLC")
        if self.ask_high < max(self.ask_open, self.ask_close) or self.ask_low > min(
            self.ask_open, self.ask_close
        ):
            raise ValueError("invalid ask OHLC")


@dataclass(frozen=True)
class Overlay:
    id: str
    kind: str
    initial_stop: Optional[float] = None
    activation: Optional[float] = None
    trail_gap: Optional[float] = None
    trail_step: Optional[float] = None
    stop_fraction: Optional[float] = None
    activation_fraction: Optional[float] = None
    trail_gap_fraction: Optional[float] = None
    target_r: Optional[float] = None


OVERLAYS = {
    "STRUCTURAL_2R": Overlay("STRUCTURAL_2R", "STRUCTURAL"),
    "US_V2_LITERAL": Overlay(
        "US_V2_LITERAL", "V2", initial_stop=1.60, activation=2.20, trail_gap=0.20
    ),
    "US_V3_005_LITERAL": Overlay(
        "US_V3_005_LITERAL", "V3", initial_stop=1.60, trail_gap=0.20, trail_step=0.05
    ),
    "US_V3_010_LITERAL": Overlay(
        "US_V3_010_LITERAL", "V3", initial_stop=1.60, trail_gap=0.20, trail_step=0.10
    ),
    "US_FIXED_2R_25PCT": Overlay(
        "US_FIXED_2R_25PCT", "PERCENT_TARGET", stop_fraction=0.25, target_r=2.0
    ),
    "US_TRAIL_30_15PCT": Overlay(
        "US_TRAIL_30_15PCT",
        "PERCENT_TRAIL",
        stop_fraction=0.25,
        activation_fraction=0.30,
        trail_gap_fraction=0.15,
    ),
}


@dataclass
class OptionReplayTrade:
    variant: str
    selector: str
    symbol: str
    direction: int
    signal_at: datetime
    entry_at: datetime
    expiry: date
    strike: float
    entry_ask: float
    entry_fill: float
    initial_debit_usd: float
    active_stop: Optional[float]
    active_target: Optional[float]
    peak_bid: float
    trail_activated: bool = False
    max_favorable_usd: float = 0.0
    max_adverse_usd: float = 0.0
    exit_at: Optional[datetime] = None
    exit_fill: Optional[float] = None
    exit_reason: Optional[str] = None
    gross_pnl_usd: Optional[float] = None
    net_pnl_usd: Optional[float] = None
    last_processed: Optional[datetime] = None


def _round_price(value: float) -> float:
    return round(value + 1e-9, 2)


def _valid_candidate(
    candidate: OptionCandidate, direction: int, observed_on: date, selector: str
) -> bool:
    expected_right = "CALL" if direction == 1 else "PUT"
    dte = (candidate.expiry - observed_on).days
    minimum_dte, maximum_dte = (5, 10) if selector == "us_balanced" else (1, 7)
    spread = candidate.ask - candidate.bid
    return (
        candidate.right == expected_right
        and minimum_dte <= dte <= maximum_dte
        and candidate.bid > 0
        and MINIMUM_PREMIUM_USD <= candidate.ask <= MAXIMUM_PREMIUM_USD
        and 0 <= spread <= MAXIMUM_SPREAD_USD
        and spread / candidate.ask <= MAXIMUM_SPREAD_FRACTION
    )


def select_contract(
    candidates: list[OptionCandidate], direction: int, observed_on: date, selector: str
) -> Optional[OptionCandidate]:
    """Select causally from the signal-time chain; never from entry-time outcomes."""
    if direction not in (-1, 1):
        raise ValueError("direction must be -1 or 1")
    if selector not in {"delta", "premium", "us_balanced"}:
        raise ValueError("selector must be delta, premium, or us_balanced")
    eligible = [
        c for c in candidates if _valid_candidate(c, direction, observed_on, selector)
    ]
    if selector == "delta":
        eligible = [
            c for c in eligible if c.delta is not None and 0.35 <= abs(c.delta) <= 0.45
        ]
    elif selector == "us_balanced":
        eligible = [
            c for c in eligible if c.delta is not None and 0.20 <= abs(c.delta) <= 0.35
        ]
    if not eligible:
        return None
    if selector == "us_balanced":
        preferred_dte = min(abs((c.expiry - observed_on).days - 7) for c in eligible)
        eligible = [
            c
            for c in eligible
            if abs((c.expiry - observed_on).days - 7) == preferred_dte
        ]
        return min(
            eligible,
            key=lambda c: (abs(abs(c.delta or 0.0) - 0.30), (c.ask - c.bid) / c.ask, c.strike),
        )
    nearest_expiry = min(c.expiry for c in eligible)
    eligible = [c for c in eligible if c.expiry == nearest_expiry]
    if selector == "delta":
        return min(
            eligible,
            key=lambda c: (abs(abs(c.delta or 0.0) - 0.40), (c.ask - c.bid) / c.ask, c.strike),
        )
    return min(eligible, key=lambda c: (abs(c.ask - 1.80), (c.ask - c.bid) / c.ask, c.strike))


class VariantBook:
    """One alternative $1,000 paper ledger; variants are never combined."""

    def __init__(self, overlay: Overlay, selector: str) -> None:
        self.overlay = overlay
        self.selector = selector
        self.completed: list[OptionReplayTrade] = []
        self.open_trade: Optional[OptionReplayTrade] = None

    def enter(
        self,
        candidate: OptionCandidate,
        signal_at: datetime,
        direction: int,
        quote: OptionQuoteBar,
    ) -> None:
        if self.open_trade is not None:
            raise RuntimeError("only one option position is allowed")
        fill = _round_price(quote.ask_open + SLIPPAGE_PER_CONTRACT_USD)
        debit = fill * CONTRACT_MULTIPLIER + COMMISSION_PER_SIDE_USD
        if fill <= MINIMUM_PREMIUM_USD:
            raise ValueError("entry fill must remain above the literal $1.60 stop")
        if debit > MAXIMUM_DEBIT_USD or debit > STARTING_CASH_USD:
            raise ValueError("entry exceeds the paper debit limit")
        active_stop = self.overlay.initial_stop
        active_target = None
        if self.overlay.stop_fraction is not None:
            active_stop = _round_price(fill * (1.0 - self.overlay.stop_fraction))
        if self.overlay.target_r is not None:
            assert active_stop is not None
            active_target = _round_price(
                fill + self.overlay.target_r * (fill - active_stop)
            )
        self.open_trade = OptionReplayTrade(
            variant=self.overlay.id,
            selector=self.selector,
            symbol=str(candidate.symbol),
            direction=direction,
            signal_at=signal_at,
            entry_at=quote.timestamp,
            expiry=candidate.expiry,
            strike=candidate.strike,
            entry_ask=quote.ask_open,
            entry_fill=fill,
            initial_debit_usd=debit,
            active_stop=active_stop,
            active_target=active_target,
            peak_bid=fill,
        )

    def process_quote(self, quote: OptionQuoteBar) -> None:
        trade = self.open_trade
        if trade is None or trade.last_processed == quote.timestamp:
            return
        trade.last_processed = quote.timestamp
        trade.max_favorable_usd = max(trade.max_favorable_usd, quote.bid_high - trade.entry_fill)
        trade.max_adverse_usd = max(trade.max_adverse_usd, trade.entry_fill - quote.bid_low)
        if self.overlay.kind == "STRUCTURAL":
            trade.peak_bid = max(trade.peak_bid, quote.bid_high)
            return
        assert trade.active_stop is not None
        if quote.bid_low <= trade.active_stop:
            raw_fill = quote.bid_open if quote.bid_open <= trade.active_stop else trade.active_stop
            self._close(
                quote.timestamp,
                raw_fill,
                "TRAIL_STOP" if trade.trail_activated else "INITIAL_STOP",
            )
            return
        if self.overlay.kind == "PERCENT_TARGET":
            assert trade.active_target is not None
            if quote.bid_high >= trade.active_target:
                raw_fill = (
                    quote.bid_open
                    if quote.bid_open >= trade.active_target
                    else trade.active_target
                )
                self._close(quote.timestamp, raw_fill, "TARGET_2R")
                return
            trade.peak_bid = _round_price(max(trade.peak_bid, quote.bid_high))
            return
        trade.peak_bid = _round_price(max(trade.peak_bid, quote.bid_high))
        if self.overlay.kind == "PERCENT_TRAIL":
            assert self.overlay.activation_fraction is not None
            assert self.overlay.trail_gap_fraction is not None
            activation = trade.entry_fill * (1.0 + self.overlay.activation_fraction)
            if trade.peak_bid >= activation:
                proposed = _round_price(
                    max(
                        trade.active_stop,
                        trade.peak_bid * (1.0 - self.overlay.trail_gap_fraction),
                    )
                )
                if proposed > trade.active_stop:
                    trade.active_stop = proposed
                    trade.trail_activated = True
            return
        proposed = self._proposed_stop(trade)
        if proposed > trade.active_stop:
            trade.active_stop = proposed
            trade.trail_activated = True

    def _proposed_stop(self, trade: OptionReplayTrade) -> float:
        assert self.overlay.initial_stop is not None and self.overlay.trail_gap is not None
        if self.overlay.kind == "V2":
            assert self.overlay.activation is not None
            return (
                self.overlay.initial_stop
                if trade.peak_bid < self.overlay.activation
                else _round_price(
                    max(self.overlay.initial_stop, trade.peak_bid - self.overlay.trail_gap)
                )
            )
        assert self.overlay.trail_step is not None
        steps = int(
            (max(0.0, trade.peak_bid - trade.entry_fill) + 1e-9) / self.overlay.trail_step
        )
        return (
            self.overlay.initial_stop
            if steps < 1
            else _round_price(
                max(
                    self.overlay.initial_stop,
                    trade.entry_fill + steps * self.overlay.trail_step - self.overlay.trail_gap,
                )
            )
        )

    def exit_at_bid_close(self, quote: OptionQuoteBar, reason: str) -> None:
        if self.open_trade is not None:
            self._close(quote.timestamp, quote.bid_close, reason)

    def _close(self, timestamp: datetime, raw_fill: float, reason: str) -> None:
        trade = self.open_trade
        assert trade is not None
        fill = _round_price(max(0.01, raw_fill - SLIPPAGE_PER_CONTRACT_USD))
        gross = (fill - trade.entry_fill) * CONTRACT_MULTIPLIER
        net = gross - 2 * COMMISSION_PER_SIDE_USD
        trade.exit_at = timestamp
        trade.exit_fill = fill
        trade.exit_reason = reason
        trade.gross_pnl_usd = round(gross, 2)
        trade.net_pnl_usd = round(net, 2)
        self.completed.append(trade)
        self.open_trade = None

    def summary(self) -> dict[str, Any]:
        values = [t.net_pnl_usd for t in self.completed if t.net_pnl_usd is not None]
        wins = [v for v in values if v > 0]
        losses = [v for v in values if v < 0]
        gross_win = sum(wins)
        gross_loss = -sum(losses)
        equity = STARTING_CASH_USD
        peak = equity
        minimum_equity = equity
        max_drawdown = 0.0
        losing_streak = 0
        longest_losing_streak = 0
        for value in values:
            equity += value
            peak = max(peak, equity)
            minimum_equity = min(minimum_equity, equity)
            max_drawdown = max(max_drawdown, peak - equity)
            losing_streak = losing_streak + 1 if value < 0 else 0
            longest_losing_streak = max(longest_losing_streak, losing_streak)
        if gross_loss > 0:
            profit_factor: Optional[float] = gross_win / gross_loss
        elif gross_win > 0:
            profit_factor = inf
        else:
            profit_factor = None
        return {
            "variant": self.overlay.id,
            "selector": self.selector,
            "trades": len(values),
            "winRate": len(wins) / len(values) if values else None,
            "netPnlUsd": round(sum(values), 2),
            "winningNetPnlUsd": round(gross_win, 2),
            "losingNetPnlUsd": round(gross_loss, 2),
            "averageNetPnlUsd": round(sum(values) / len(values), 2) if values else None,
            "profitFactor": profit_factor,
            "maxDrawdownUsd": round(max_drawdown, 2),
            "peakEquityUsd": round(peak, 2),
            "minimumEquityUsd": round(minimum_equity, 2),
            "capitalBelowMaximumDebit": minimum_equity < MAXIMUM_DEBIT_USD,
            "capitalExhausted": minimum_equity <= 0,
            "longestLosingStreak": longest_losing_streak,
            "endingPaperCashUsd": round(STARTING_CASH_USD + sum(values), 2),
            "tradesDetail": [asdict(t) for t in self.completed],
        }


class OptionReplayEngine:
    def __init__(self, selector: str) -> None:
        if selector not in {"delta", "premium", "us_balanced"}:
            raise ValueError("selector must be delta, premium, or us_balanced")
        self.selector = selector
        self.books = {
            name: VariantBook(overlay, selector) for name, overlay in OVERLAYS.items()
        }
        self.rejections: dict[str, int] = {}
        self.cohorts_entered = 0

    @property
    def open_symbol(self) -> Optional[str]:
        for book in self.books.values():
            if book.open_trade is not None:
                return book.open_trade.symbol
        return None

    @property
    def structural_open(self) -> bool:
        return self.books["STRUCTURAL_2R"].open_trade is not None

    def reject(self, reason: str) -> None:
        self.rejections[reason] = self.rejections.get(reason, 0) + 1

    def enter(
        self,
        candidate: OptionCandidate,
        signal_at: datetime,
        direction: int,
        quote: OptionQuoteBar,
    ) -> bool:
        spread = quote.ask_open - quote.bid_open
        if (
            spread < 0
            or spread > MAXIMUM_SPREAD_USD
            or spread / quote.ask_open > MAXIMUM_SPREAD_FRACTION
        ):
            self.reject("ENTRY_QUOTE_TOO_WIDE_OR_CROSSED")
            return False
        fill = _round_price(quote.ask_open + SLIPPAGE_PER_CONTRACT_USD)
        debit = fill * CONTRACT_MULTIPLIER + COMMISSION_PER_SIDE_USD
        if fill <= MINIMUM_PREMIUM_USD:
            self.reject("entry fill must remain above the literal $1.60 stop")
            return False
        if debit > MAXIMUM_DEBIT_USD or debit > STARTING_CASH_USD:
            self.reject("entry exceeds the paper debit limit")
            return False
        if any(book.open_trade is not None for book in self.books.values()):
            raise RuntimeError("only one option cohort is allowed")
        for book in self.books.values():
            book.enter(candidate, signal_at, direction, quote)
        self.cohorts_entered += 1
        return True

    def process_quote(self, quote: OptionQuoteBar) -> None:
        for book in self.books.values():
            book.process_quote(quote)

    def structural_exit(self, quote: OptionQuoteBar, reason: str) -> None:
        self.books["STRUCTURAL_2R"].exit_at_bid_close(quote, reason)

    def force_exit(self, quote: OptionQuoteBar) -> None:
        for book in self.books.values():
            book.exit_at_bid_close(quote, "SESSION_EXIT")

    def summaries(self) -> dict[str, dict[str, Any]]:
        return {name: book.summary() for name, book in self.books.items()}
