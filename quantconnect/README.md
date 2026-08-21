# QuantConnect entry backtest

This project is the free-cloud backtest path for the US Options Lab. QuantConnect provides SPY minute history in its cloud. No market-data file, API key, or licensed data is committed here.

## What this stage tests

The first stage tests only two SPY underlying entry families:

- `US_OPENING_DRIVE`
- `US_FAILED_OPEN_BREAK`

Each runs independently, takes no more than one virtual trade per session, enters at the next minute's open after a completed-bar signal, uses a structural stop and 2R target, assumes stop-first ordering when a bar touches both levels, and exits by 15:45 ET.

This is deliberately not yet an options backtest. The $1,000 cash ledger, option selection, bid/ask execution, and US V2/V3 exits are Phase 3. Those tests are meaningful only if at least one underlying entry family survives development and validation.

## Frozen periods

| Parameter | Dates | Purpose |
|---|---|---|
| `development` | 2018-01-01 through 2022-12-31 | Initial evidence |
| `validation` | 2023-01-01 through 2024-12-31 | Out-of-sample check |
| not exposed | 2025 onward | Untouched holdout |

Do not change thresholds after inspecting validation. Do not run 2025+ until the repository records a final strategy and options-execution specification.

## Run in QuantConnect Cloud

1. Create a free QuantConnect account and a Python project.
2. Replace the project's `main.py` with this directory's `main.py`.
3. Add `strategy_core.py` as a second project file.
4. Set project parameter `period` to `development` and run a backtest.
5. Save the backtest ID and compact log summaries before running `validation`.
6. Compare trade count, average R, total R, profit factor, drawdown, and losing streak. Never combine the two strategies' R as one account result.

The wrapper never calls `market_order`, `set_holdings`, or any other order method. All trades are virtual records inside `strategy_core.py`.

Free QuantConnect data remains inside QuantConnect Cloud. GitHub Actions therefore tests the simulator for causality and safety but cannot launch the free cloud backtest automatically.
