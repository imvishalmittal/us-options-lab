# SPY Intraday V2 Underlying Backtest Results

Run date: 2026-08-24

## Protocol

- Source: Alpaca historical SPY SIP one-minute bars.
- Session: 09:30 through 15:59 America/New_York; extended-hours bars removed.
- Execution: signals on completed bars, entry on the next bar open, adverse
  gaps through a stop filled at the next available open, and no overnight hold.
- Returns are normalized to the initial underlying stop (`R`). They are not
  option returns and do not include option spreads, commissions, or slippage.
- The rules in `ENTRY_V2_SPEC.md` were not tuned between years.

## Noise-Area Momentum

| Year | Role | Trades | Win rate | Average R | Total R | Profit factor | Max drawdown R |
|---:|---|---:|---:|---:|---:|---:|---:|
| 2018 | Development | 148 | 33.1% | +0.259 | +38.27 | 1.61 | 12.72 |
| 2019 | Development | 124 | 35.5% | +0.080 | +9.88 | 1.19 | 8.68 |
| 2020 | Development | 135 | 37.8% | +0.251 | +33.92 | 1.62 | 11.53 |
| 2021 | Development | 135 | 48.1% | +0.542 | +73.21 | 2.63 | 7.96 |
| 2022 | Development | 142 | 35.9% | +0.237 | +33.72 | 1.59 | 7.18 |
| 2023 | Untouched validation | 149 | 38.3% | +0.144 | +21.40 | 1.34 | 17.49 |
| 2024 | Secondary validation | 144 | 36.1% | +0.199 | +28.64 | 1.49 | 9.17 |

Development aggregate (2018–2022): 684 trades, +189.01R, +0.276R per
trade, and profit factor 1.70. Every development year was positive.

The full 2024 calendar year was fetched by the Alpaca validation runner. January
2024 had previously been viewed during option-data feasibility work, so 2024 is
reported only as secondary validation rather than a pristine holdout. The
untouched 2023 validation result independently remained positive.

Decision: **promote only to option replay**. This does not establish that a
long-call/long-put implementation is profitable after bid/ask spread, theta,
contract selection, fees, and capital limits.

## Closing-Half-Hour Momentum

| Year | Trades | Average R | Total R | Profit factor |
|---:|---:|---:|---:|---:|
| 2018 | 121 | +0.074 | +9.01 | 1.26 |
| 2019 | 117 | +0.010 | +1.18 | 1.05 |
| 2020 | 129 | -0.076 | -9.78 | 0.83 |
| 2021 | 111 | -0.040 | -4.49 | 0.83 |
| 2022 | 133 | -0.006 | -0.75 | 0.98 |

Development aggregate: 611 trades, -4.83R, -0.008R per trade, and profit
factor 0.97.

Decision: **reject**. Do not run validation, option replay, or forward paper
trading for this strategy.

## Next gate

1. Replay Noise-Area signals against historical SPY option bid/ask bars.
2. Predeclare contract selection: one contract, at least one full DTE, maximum
   $220 debit, with delta/debit selection evaluated before fixed premium.
3. Model ask entry, bid exit, commissions, spread, and conservative slippage.
4. Use separate $1,000 paper ledgers with at most $10 planned risk per trade;
   reject any contract that cannot respect the debit and risk constraints.
5. Keep 2025 onward sealed as the final holdout until the option implementation
   passes development and validation.
