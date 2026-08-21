# US Options Lab

A separate, research-only laboratory for systematic US options strategies. It places no broker orders and must not be treated as a live-trading system.

## Foundation scope

- $1,000 simulated starting capital in a cash-only paper account
- SPY long calls or long puts
- One simulated contract and no more than one open position
- Maximum initial option debit of $220
- At least one full day to expiry; no 0DTE
- Forced same-day exit by 15:45 ET
- Buy at observable ask and sell at observable bid
- Full commissions, fees, spread, and slippage
- No short options, spreads, overnight holding, exercise, or assignment

Two future contract-selection hypotheses remain predeclared: closest eligible contract to $1.80 within $1.60–$2.20, and absolute delta 0.35–0.45 with debit no greater than $220.

## Strategy architecture

US entries are separate from the NIFTY lab:

- Opening Drive Continuation
- Failed Opening Break Reversal
- Midday Compression Breakout (deferred)
- Power-Hour Momentum (deferred)

NIFTY V2 and V3 are not US entry strategies. Their literal $1.80/$1.60/$2.20 translations remain secondary option-exit benchmarks. The primary exit benchmark is an underlying-structure stop with a 2R target.

## Current status

The first two SPY entry rules are frozen and implemented as an order-free QuantConnect/LEAN research package. QuantConnect is the primary free cloud-data path; Databento is retained only as an optional independent, high-resolution quote verification path.

The next evidence steps are:

1. Run 2018–2022 development in QuantConnect Cloud.
2. Without changing thresholds, run 2023–2024 validation.
3. Reject any entry family that fails either period.
4. Only then add option selection, $1,000 ledger accounting, bid/ask fills, and structural versus V2/V3 exit comparisons.

The 2025+ holdout is intentionally unavailable in executable parameters. No candidate strategy is paper-enabled.

## Safety boundary

- `mode` remains `RESEARCH_ONLY`.
- The $1,000 is simulated and cannot fund or place an order.
- The QuantConnect wrapper contains no order calls.
- No broker integration, live orders, or licensed raw market data.
- This repository shares no workflows, state, or credentials with `nifty-options-lab`.

## Run local tests

Requires Node.js 20 or newer and Python 3.10 or newer.

```bash
npm test
npm run check
python -m py_compile quantconnect/strategy_core.py quantconnect/main.py
python -m unittest discover -s test_python -p 'test_*.py'
```

Run the actual historical study in QuantConnect Cloud using [the QuantConnect instructions](quantconnect/README.md).

## Documentation

- [Research protocol](docs/RESEARCH_PROTOCOL.md)
- [Frozen SPY Entry V1 specification](docs/ENTRY_V1_SPEC.md)
- [US strategy research](docs/STRATEGY_RESEARCH.md)
- [Historical-data feasibility](docs/DATA_FEASIBILITY.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
