# US Strategy Research

## Decision

US entries will not be copied from the NIFTY lab. The NIFTY V2 and V3 rules are option-premium exit methods, not complete entry strategies. They remain literal, secondary exit benchmarks while SPY-specific entry hypotheses are tested independently.

Nothing in this catalog is paper-enabled.

## Why the day is split into regimes

US equity-market volatility and volume are typically U-shaped, with unusually active price discovery near the open and renewed activity near the close. That supports separate open, midday, and power-hour hypotheses rather than one all-day rule.

Published research found that the first half-hour SPY return predicted the final half-hour over 1993–2013, especially on high-volatility and high-volume days. Later out-of-sample research found that this predictability disappeared without regime conditioning. Power-hour momentum is therefore a candidate to falsify, not an accepted edge.

Sources:

- [Market intraday momentum, Journal of Financial Economics](https://doi.org/10.1016/j.jfineco.2018.05.009)
- [Understanding intraday momentum strategies, Journal of Futures Markets](https://doi.org/10.1002/fut.22375)
- [Intraday volatility and the opening spike](https://doi.org/10.1111/1468-2362.00103)

## Entry candidates

### E1 — Opening Drive Continuation

Observe 09:30–09:45 ET. Between 09:45 and 10:30, test continuation only when the opening-range break is accepted and agrees with VWAP, relative volume, and realized-volatility conditions.

### E2 — Failed Opening Break Reversal

Observe 09:30–10:00. Test a reversal only after price breaks an opening-range edge, closes back inside, and confirms rejection around VWAP. This is distinct from momentum and targets false opening moves.

### E3 — Midday Compression Breakout

Observe 10:30–12:30. Test a later break between 12:30 and 14:00 only after measurable range/volatility compression and renewed volume. This provides a second opportunity window when no opening setup qualifies.

### E4 — Power-Hour Momentum

Use the first-half-hour move, full-session direction, VWAP location, relative volume, and realized volatility. Permit a signal only between 15:00 and 15:15, with forced exit by 15:45. The out-of-sample failure reported in later research makes strong regime conditioning mandatory.

## Exits

The primary benchmark will be an underlying-structure stop with a fixed 2R target. Only entry families that survive underlying-level development and validation proceed to option replay.

The secondary exit benchmarks are literal 100:1 translations of the NIFTY premium rules:

| Overlay | Initial stop | Activation | Trail |
|---|---:|---:|---:|
| US V2 literal | $1.60 | $2.20 | continuous $0.20 gap |
| US V3 literal 5 | $1.60 | first $0.05 favorable step | $0.05 steps with $0.20 gap |
| US V3 literal 10 | $1.60 | first $0.10 favorable step | $0.10 steps with $0.20 gap |

All share a premium reference around $1.80. These absolute thresholds may fit NIFTY and fail on SPY; that is precisely what the benchmark will test. No threshold will be changed after validation begins.

## Anti-overfitting sequence

1. Evaluate each entry hypothesis on SPY itself using causal one-minute data.
2. Reject entry families that fail predeclared development and validation gates.
3. Replay only surviving entries through options using the delta/debit selector first.
4. Compare the structural exit with V2 and V3 on the identical trade cohort.
5. Test the fixed-$1.80 selector only as a separate contract-selection hypothesis.
6. Preserve a final untouched holdout period.

This sequence avoids testing every entry × selector × exit combination and choosing the luckiest result.

## Deferred

The following are intentionally excluded from the first study: 0DTE, short premium, straddles, spreads, earnings trades, individual-stock options, pure unconditioned VWAP mean reversion, and forced daily trading.
