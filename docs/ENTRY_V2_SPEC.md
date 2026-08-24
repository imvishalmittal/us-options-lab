# Frozen SPY Intraday V2 Entry Specification

Status: frozen before results; underlying development and validation completed
with Alpaca SIP minute bars on 2026-08-24. See
`INTRADAY_V2_BACKTEST_RESULTS.md`.

## Research boundary

- SPY underlying bars only at this gate; no option P/L yet.
- One-minute regular-session data and next-bar-open entries.
- Strategies are independent alternatives and their returns are never added.
- One virtual trade per strategy per session.
- 2018–2022 development, 2023 validation, February–December 2024 secondary
  validation, and 2025 onward reserved as the final post-publication holdout.
- January 2024 is excluded because it was previously inspected during option
  replay feasibility work.
- No parameter search after a result is observed.

## V2-E1 — Gap-adjusted Noise-Area Momentum

1. For every minute of the regular session, calculate the absolute move from
   that session's open over the preceding 14 completed sessions.
2. Anchor the upper band to the greater of today's open and yesterday's close;
   anchor the lower band to the lesser value. Apply the mean historical move
   for the matching minute to those anchors.
3. Check only at 30-minute checkpoints from 10:00 through 15:00 ET.
4. A close above the upper band and VWAP signals long; a close below the lower
   band and VWAP signals short.
5. Enter on the next minute's open with the completed signal-bar VWAP as the
   initial stop. Reject a gap that invalidates the stop.
6. Ratchet the stop using completed-bar VWAP, effective only on the next bar.
7. Close any remainder through the exchange-calendar callback before the end
   of the session.

This is a causal, non-leveraged underlying replication of the published
"out-of-noise" hypothesis. Volatility targeting and parameter optimization are
intentionally omitted.

## V2-E2 — Closing-Half-Hour Momentum

1. Measure the first half-hour return from the prior close through 09:59 ET.
2. Measure the penultimate half-hour return from 14:59 through 15:29 ET.
3. When both returns have the same non-zero sign, signal in that direction at
   15:29 and enter on the 15:30 minute's open.
4. Use a fixed 0.30% underlying stop from the signal close; reject an entry gap
   that invalidates it.
5. Exit at 15:55 ET. The exchange-calendar callback is the backstop for early
   closes and missing final bars.

## Promotion gate

A strategy reaches option replay only if development has positive average R,
profit factor above 1, non-trivial trades across multiple years, tolerable
drawdown, and no dependence on one year or a few outliers. Passing this gate is
necessary, not evidence of live profitability.

Noise-Area Momentum passed this underlying-only gate. Closing-Half-Hour
Momentum failed it and is retired. No V2 strategy is approved for paper options
until causal option bid/ask replay, costs, contract selection, and the $1,000
capital constraints are evaluated.
