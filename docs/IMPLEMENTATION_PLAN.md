# Implementation Plan

## Status

Strategy catalog and causal quote/exit primitives are implemented. No market-data provider has been approved and no strategy backtest has been run.

## Phase 0 — Repository foundation

- [x] Research-only configuration with executable safety checks
- [x] $1,000 cash-only paper-account baseline
- [x] One-position and $220 maximum-initial-debit limits
- [x] SPY-only initial scope
- [x] Fixed-premium and delta/debit contract-selection hypotheses
- [x] CI syntax and regression tests
- [x] Research protocol and data-quality gates

## Phase 1 — Historical-data and strategy feasibility

- [x] Define four US-specific entry candidates across open, midday, and power hour
- [x] Preserve V2/V3 only as disabled secondary exit benchmarks
- [x] Define provider-neutral ordered quote observations and minute bid/ask bars
- [x] Reject crossed, invalid, and zero-size quotes with reason codes
- [x] Shortlist Databento OPRA as the preferred small pilot
- [ ] Add an authenticated provider adapter after a key is configured
- [ ] Run `metadata.get_cost` before downloading any OPRA data
- [ ] Evaluate five non-consecutive SPY sessions across volatility regimes
- [ ] Measure missing, stale, crossed, and zero-size quotes
- [ ] Verify US holiday, early-close, and daylight-saving behavior
- [ ] Produce a go/no-go feasibility report from actual pilot data

Exit criterion: a reproducible sample proves that causal expired-contract bid/ask reconstruction is possible at an acceptable cost. Otherwise stop the options backtest.

## Phase 2 — Underlying entry backtests

- [ ] Freeze numeric entry thresholds using development data only
- [ ] Test Opening Drive and Failed Open Break first
- [ ] Test Midday Compression only after the opening study is frozen
- [ ] Test Power-Hour Momentum with explicit out-of-sample skepticism
- [ ] Reject entry families that fail development and validation
- [ ] Preserve an untouched holdout period

Exit criterion: only entry families with stable SPY-level evidence proceed to option replay.

## Phase 3 — Options replay

- [ ] Implement causal contract selection
- [ ] Model the single $1,000 paper ledger and available cash
- [ ] Model ask entry, bid exit, commissions, fees, and slippage
- [ ] Compare the structural 2R exit against V2 and V3 on identical cohorts
- [ ] Add adverse handling for unresolved intrabar ambiguity
- [ ] Persist rejected observations with explicit reason codes
- [ ] Compare delta/debit selection before the fixed-$1.80 selector

Exit criterion: deterministic replay, full audit trail, zero look-ahead violations, and robust validation/holdout results.

## Phase 4 — Research decision

- [ ] Evaluate expectancy, concentration, drawdown, and losing streak
- [ ] Reject strategies that depend on one period or a few outliers
- [ ] Publish a signed-off research report

Exit criterion: either reject the strategy or authorize forward paper observation. Historical profit alone is insufficient.

## Phase 5 — Forward paper lab

- [ ] Add short scheduled checkpoints rather than a market-long job
- [ ] Persist resumable session state and the $1,000 paper ledger
- [ ] Build a date-wise dashboard
- [ ] Add data-health and duplicate-session guards
- [ ] Accumulate a predeclared minimum evidence window

Live trading is out of scope. The current India-resident setup must not be assumed to permit overseas derivatives.
