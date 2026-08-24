# US Options Lab

A separate, research-only laboratory for systematic US options strategies. It places no broker orders and must not be treated as a live-trading system.

## Foundation scope

- $1,000 simulated starting capital in a cash-only paper account
- SPY long calls or long puts
- One simulated contract and no more than one open position
- Maximum initial option debit of $220
- At least one full day to expiry; no 0DTE
- Forced same-day exit 15 minutes before the exchange's actual close
- Buy at observable ask and sell at observable bid
- Full commissions, fees, spread, and slippage
- No short options, spreads, overnight holding, exercise, or assignment

Three contract selectors are reproducible: closest eligible contract to $1.80,
absolute delta 0.35–0.45 at 1–7 DTE, and a US-balanced 5–10 DTE selector near
0.30 delta. All remain research-only.

## Strategy architecture

US entries are separate from the NIFTY lab:

- Opening Drive Continuation
- Failed Opening Break Reversal
- Midday Compression Breakout (deferred)
- Power-Hour Momentum (deferred)

NIFTY V2 and V3 are not US entry strategies. Their literal $1.80/$1.60/$2.20 translations remain secondary option-exit benchmarks. The primary exit benchmark is an underlying-structure stop with a 2R target.

The replay also includes two US-scaled controls: a 25%-premium-risk 2R exit
and a percentage trail that activates at +30% and stays 15% below the peak.

## Current status

The order-free QuantConnect study is complete. Opening Drive passed the SPY
underlying gate, but every tested long-option implementation failed development.
The literal delta cohort lost $3,048.50 to $3,257.50 across 405 trades depending
on exit. The US-balanced structural candidate was slightly positive in 2018
and 2019, then failed the 2020 stress year and ended negative in aggregate.

No candidate is authorized for forward paper automation. Full evidence and
QuantConnect algorithm IDs are in
[SPY option replay results](docs/OPTION_REPLAY_RESULTS.md).

The 2025+ holdout is intentionally unavailable in executable parameters. No candidate strategy is paper-enabled.

The next frozen entry cycle is specified separately in
[SPY Intraday V2](docs/ENTRY_V2_SPEC.md): gap-adjusted Noise-Area Momentum and
Closing-Half-Hour Momentum. [Intraday V2 results](docs/INTRADAY_V2_BACKTEST_RESULTS.md)
show that Noise-Area passed the underlying development/validation gate and
Closing-Half-Hour was rejected. Noise-Area still requires a cost-aware option
replay before any forward paper session.

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
- [Frozen SPY Intraday V2 specification](docs/ENTRY_V2_SPEC.md)
- [US strategy research](docs/STRATEGY_RESEARCH.md)
- [Historical-data feasibility](docs/DATA_FEASIBILITY.md)
- [Implementation plan](docs/IMPLEMENTATION_PLAN.md)
- [SPY option replay results](docs/OPTION_REPLAY_RESULTS.md)
