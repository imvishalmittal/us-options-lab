# Implementation Plan

## Status

The strategy catalog, causal quote/exit primitives, and a QuantConnect-ready underlying entry simulator are implemented. No strategy result has yet been accepted, no options replay has run, and no candidate is paper-enabled.

## Phase 0 — Repository foundation

- [x] Research-only configuration with executable safety checks
- [x] $1,000 cash-only paper-account baseline
- [x] One-position and $220 maximum-initial-debit limits
- [x] SPY-only initial scope
- [x] Fixed-premium and delta/debit contract-selection hypotheses
- [x] CI syntax and regression tests
- [x] Research protocol and data-quality gates

## Phase 1 — Data paths

- [x] Define provider-neutral ordered option-quote observations and minute bid/ask bars
- [x] Add a bounded, metadata-only Databento cost estimator
- [x] Select QuantConnect Cloud as the free primary backtest environment
- [x] Keep licensed QuantConnect data inside QuantConnect Cloud
- [ ] Use Databento only for an optional independent high-resolution quote pilot

QuantConnect's free cloud data is sufficient for the initial SPY entry study and later minute-level option research. Databento remains useful if event ordering or independent fill verification is required; no paid download is authorized by this plan.

## Phase 2 — Underlying entry backtests

- [x] Freeze Opening Drive and Failed Open Break V1 rules
- [x] Implement a provider-neutral, order-free causal simulator
- [x] Add a QuantConnect Cloud wrapper for development and validation
- [x] Exclude 2025+ holdout from executable parameters
- [ ] Run 2018–2022 development in QuantConnect and record the backtest ID
- [ ] Run 2023–2024 validation without changing thresholds
- [ ] Reject entry families that fail either period
- [ ] Consider Midday Compression only after the opening study decision
- [ ] Consider Power-Hour Momentum as a separately frozen study

Exit criterion: only entry families with stable SPY-level evidence proceed to option replay.

## Phase 3 — Options replay

- [ ] Subscribe to SPY option chains with at least one full DTE
- [ ] Implement causal contract selection
- [ ] Model the single $1,000 ledger and available cash
- [ ] Model ask entry, bid exit, commissions, fees, spread, and slippage
- [ ] Compare structural 2R against V2 and V3 on the identical trade cohort
- [ ] Add adverse handling for unresolved intrabar ambiguity
- [ ] Compare delta/debit selection before the fixed-$1.80 selector
- [ ] Preserve 2025+ as final holdout until the full specification is frozen

Exit criterion: deterministic replay, full audit trail, zero look-ahead violations, and robust validation/holdout results.

## Phase 4 — Research decision

- [ ] Evaluate expectancy, concentration, drawdown, and losing streak
- [ ] Reject strategies that depend on one period or a few outliers
- [ ] Publish a signed-off research report

Exit criterion: reject the strategy or authorize forward paper observation. Historical profit alone is insufficient.

## Phase 5 — Forward paper lab

- [ ] Add short scheduled checkpoints rather than a market-long job
- [ ] Persist resumable session state and the $1,000 paper ledger
- [ ] Build a date-wise dashboard
- [ ] Add data-health and duplicate-session guards
- [ ] Accumulate a predeclared minimum evidence window

Live trading is out of scope. The current India-resident setup must not be assumed to permit overseas derivatives.
