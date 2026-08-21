# US Options Lab

A separate, research-only laboratory for testing systematic US options strategies. It does not place broker orders and must not be treated as a live-trading system.

## Foundation scope

- $1,000 simulated starting capital in a cash-only paper account
- SPY long calls or long puts
- One simulated contract and no more than one open position
- Maximum initial option debit of $220
- One-minute causal market data derived from ordered bid/ask observations
- At least one full day to expiry; no 0DTE
- Forced same-day exit by 15:45 ET
- Buy at the recorded ask and sell at the recorded bid
- Full commissions, fees, spread, and slippage
- No short options, spreads, overnight holding, exercise, or assignment

Two contract-selection hypotheses will eventually be compared:

1. Contract closest to a $1.80 premium within $1.60–$2.20.
2. Contract with absolute delta 0.35–0.45 and debit no greater than $220.

## Strategy architecture

US entry hypotheses are deliberately separate from the NIFTY lab:

- Opening Drive Continuation
- Failed Opening Break Reversal
- Midday Compression Breakout
- Power-Hour Momentum

NIFTY V2 and V3 are not treated as US entry strategies. Their $1.80/$1.60/$2.20 literal translations are implemented only as secondary exit benchmarks. The primary benchmark is an underlying-structure stop with a 2R target.

All candidates and overlays remain `paperEnabled: false` until the historical-data and backtest gates pass.

## Current status

**Strategy catalog, causal exit/quote primitives, and a metadata-only Databento cost estimator are implemented. No backtest has been run and no market data has been downloaded.**

The preferred feasibility pilot is historical SPY OPRA data with ordered NBBO observations. A last quote at each minute is not sufficient to reconstruct within-minute V2/V3 peaks and stops; the pilot requires one-second or event-level quotes from which bid/ask bars can be derived.

The manual `Databento cost estimate` workflow calls only `metadata.get_cost`. It is capped at seven days and records `download_performed: false`. Add `DATABENTO_API_KEY` as a repository Actions secret before running it; never paste the key into an issue, workflow input, commit, or chat.

## Safety boundary

- `mode` is hard-coded to `RESEARCH_ONLY`.
- The $1,000 balance is simulated and cannot fund or place an order.
- Live orders and broker integration are disabled and regression-tested.
- No candidate strategy is paper-enabled.
- The repository must not contain broker credentials or licensed raw data.
- The present India-resident setup must not be assumed to permit overseas derivatives.

## Run locally

Requires Node.js 20 or newer.

```bash
npm test
npm run check
python -m unittest discover -s test_python -p 'test_*.py'
node src/cli.mjs
```

## Documentation

- [Research protocol](docs/RESEARCH_PROTOCOL.md)
- [US strategy research](docs/STRATEGY_RESEARCH.md)
- [Historical-data feasibility](docs/DATA_FEASIBILITY.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)

## Relationship to the NIFTY lab

This repository is completely separate from `nifty-options-lab`. It shares no workflows, journals, credentials, schedules, or strategy state.
