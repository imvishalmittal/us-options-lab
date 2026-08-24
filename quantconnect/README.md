# QuantConnect underlying and option backtests

This project is the free-cloud backtest path for the US Options Lab. QuantConnect provides SPY minute history in its cloud. No market-data file, API key, or licensed data is committed here.

## What this stage tests

The first stage tests only two SPY underlying entry families:

- `US_OPENING_DRIVE`
- `US_FAILED_OPEN_BREAK`

Each runs independently, takes no more than one virtual trade per session, enters at the next minute's open after a completed-bar signal, uses a structural stop and 2R target, assumes stop-first ordering when a bar touches both levels, and exits 15 minutes before the exchange's actual close (including early-close sessions).

`options_main.py` performs the separate long-option replay after an underlying
entry family passes. It uses `option_replay_core.py`, separate $1,000 ledgers,
ask/bid execution, costs, capital-breach flags, structural exits, literal V2/V3,
and US-scaled percentage exits. It never calls a LEAN order API.

`intraday_v2_main.py` is a separate underlying-only wrapper for the frozen V2
cycle. It runs Noise-Area Momentum and Closing-Half-Hour Momentum from
`intraday_v2_core.py`; it does not reuse or modify V1.

`qc_intraday_v2_self_contained.py` is the equivalent single-file cloud harness.
It exists to avoid cloud-editor synchronization issues and remains order-free.

## Frozen periods

| Parameter | Dates | Purpose |
|---|---|---|
| `development` | 2018-01-01 through 2022-12-31 | Initial evidence |
| `validation` | 2023-01-01 through 2024-12-31 | Out-of-sample check |
| not exposed | 2025 onward | Untouched holdout |

Do not change thresholds after inspecting validation. Do not run 2025+ until the repository records a final strategy and options-execution specification.

## Run in QuantConnect Cloud

1. Create a free QuantConnect account and a Python project.
2. For the underlying study, replace the project's `main.py` with this
   directory's `main.py` and add `strategy_core.py`.
3. For option replay, use `options_main.py` as cloud `main.py` and add both
   `strategy_core.py` and `option_replay_core.py`.
4. For Intraday V2, use `intraday_v2_main.py` as cloud `main.py` and add
   `strategy_core.py` plus `intraday_v2_core.py`.
   Alternatively, copy `qc_intraday_v2_self_contained.py` directly to cloud
   `main.py` without adding any helper files.
5. Set project parameter `period` to the appropriate development slice and run
   a backtest.
6. Save the backtest ID and compact log summaries before running validation.
7. Compare trade count, average R, total R, profit factor, drawdown, and losing
   streak. Never combine alternative strategies as one account result.

The wrapper never calls `market_order`, `set_holdings`, or any other order method. All trades are virtual records inside `strategy_core.py`.

Available option selectors are `delta`, `premium`, and `us_balanced`. The
executable periods include annual development slices for safe aggregation;
2025+ remains unavailable. The completed results reject every tested option
candidate; see `docs/OPTION_REPLAY_RESULTS.md`.

Free QuantConnect data remains inside QuantConnect Cloud. GitHub Actions
therefore tests the simulator for causality and safety but cannot launch the
free cloud backtest automatically.

## Current cloud checkpoint

- Clean project: https://www.quantconnect.com/project/35552604
- Project name: `Sleepy Orange Guanaco`
- The single-file 2018 development harness compiles successfully.
- QuantConnect currently blocks the first backtest until the account is
  verified by linking a credit card. No card details were entered and no
  backtest result exists yet.
