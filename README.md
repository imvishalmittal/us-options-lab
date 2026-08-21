# US Options Lab

A separate, research-only laboratory for testing systematic US options strategies. It does not place broker orders and must not be treated as a live-trading system.

## Foundation scope

The first study is intentionally narrow:

- $1,000 simulated starting capital in a cash-only paper account
- SPY long calls or long puts
- One simulated contract and no more than one open position
- Maximum initial option debit of $220
- One-minute causal market data
- At least one full day to expiry; no 0DTE
- Entry research window: 09:35–10:00 ET
- Forced same-day exit: 15:45 ET
- Buy at the recorded ask and sell at the recorded bid
- Full commissions, fees, spread, and slippage
- No short options, spreads, overnight holding, exercise, or assignment

Two predeclared contract-selection hypotheses will be compared:

1. Contract closest to a $1.80 premium within $1.60–$2.20.
2. Contract with absolute delta 0.35–0.45 and debit no greater than $220.

These are research hypotheses, not recommendations.

## Current status

**Foundation only. No backtest has been run. No data provider has been approved.**

The next gate is a historical-data feasibility study. We need reliable expired SPY option quotes with one-minute bid/ask data. Option OHLC alone is not sufficient for a credible execution backtest.

If that evidence is unavailable or too costly, this options study stops and the fallback becomes a cash SPY/QQQ ETF research track.

## Safety boundary

- `mode` is hard-coded to `RESEARCH_ONLY`.
- The $1,000 balance is simulated and cannot fund or place an order.
- Live orders and broker integration are disabled and regression-tested.
- The repository must not contain broker credentials or order endpoints.
- The present India-resident setup must not be assumed to permit overseas derivatives.

## Run locally

Requires Node.js 20 or newer.

```bash
npm test
npm run check
node src/cli.mjs
```

## Documentation

- [Research protocol](docs/RESEARCH_PROTOCOL.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)

## Relationship to the NIFTY lab

This repository is completely separate from `nifty-options-lab`. It shares no workflows, journals, credentials, schedules, or strategy state.
