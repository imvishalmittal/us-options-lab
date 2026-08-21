# Implementation Plan

## Status

Foundation setup. No market-data provider has been approved and no strategy backtest has been run.

## Phase 0 — Repository foundation

- [x] Research-only configuration with executable safety checks
- [x] $1,000 cash-only paper-account baseline
- [x] One-position and $220 maximum-initial-debit limits
- [x] SPY-only initial scope
- [x] Fixed-premium and delta/debit contract-selection hypotheses
- [x] CI syntax and regression tests
- [x] Research protocol and data-quality gates

## Phase 1 — Historical-data feasibility

- [ ] Define a provider-neutral one-minute option quote interface
- [ ] Evaluate coverage for expired SPY contracts, bid/ask quotes, and timestamps
- [ ] Measure missing, stale, crossed, and zero-size quotes
- [ ] Verify US holiday, early-close, and daylight-saving behavior
- [ ] Estimate data cost before purchasing or running a large extraction
- [ ] Produce a go/no-go feasibility report

Exit criterion: a reproducible sample proves that causal, one-minute, expired-contract bid/ask reconstruction is possible. Otherwise stop the options backtest.

## Phase 2 — Backtest engine

- [ ] Freeze V1 entry and exit rules before loading validation data
- [ ] Implement causal contract selection
- [ ] Model the single $1,000 paper ledger and available cash
- [ ] Model ask entry, bid exit, commissions, fees, and slippage
- [ ] Add adverse handling for ambiguous intrabar exits
- [ ] Persist rejected observations with explicit reason codes
- [ ] Separate development, validation, and untouched holdout periods

Exit criterion: deterministic replay, full audit trail, and zero look-ahead violations in tests.

## Phase 3 — Research decision

- [ ] Compare fixed-premium and delta/debit selectors
- [ ] Evaluate robustness, concentration, drawdown, and losing streak
- [ ] Reject strategies that depend on one period or a few outliers
- [ ] Publish a signed-off research report

Exit criterion: either reject the strategy or authorize forward paper observation. Historical profit alone is insufficient.

## Phase 4 — Forward paper lab

- [ ] Add short scheduled checkpoints rather than a market-long job
- [ ] Persist resumable session state and the $1,000 paper ledger
- [ ] Build a date-wise dashboard
- [ ] Add data-health and duplicate-session guards
- [ ] Accumulate a predeclared minimum evidence window

Live trading is out of scope. The current India-resident setup must not be assumed to permit overseas derivatives.
