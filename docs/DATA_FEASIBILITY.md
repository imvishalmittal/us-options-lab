# Historical Options Data Feasibility

Status as of 2026-08-21: **QuantConnect Cloud selected for the free research path; no paid download authorized.**

## Primary path: QuantConnect Cloud

QuantConnect's AlgoSeek US Equity Options dataset is available without a separate data subscription for cloud backtests. It includes minute trade and quote bars, option contract metadata, and separate bid/ask quote-bar fields. The history begins in 2012, which is sufficient for the predeclared development and validation periods.

The free data is used inside QuantConnect Cloud. It is not copied to this repository, exported as licensed raw data, or assumed to be available to GitHub Actions. The free account's cloud backtest must therefore be launched from a QuantConnect project.

Official references:

- [AlgoSeek US Equity Options dataset](https://www.quantconnect.com/data/algoseek-us-equity-options)
- [Equity-options historical data](https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/asset-classes/equity-options)
- [Cloud backtest deployment](https://www.quantconnect.com/docs/v2/cloud-platform/backtesting/deployment)

## Resolution limitation

Minute option quote bars provide bid and ask OHLC but cannot always establish the ordering of a peak and trailing-stop touch within the same minute. The research protocol must use adverse stop-first handling when ordering is ambiguous. If a strategy's apparent edge depends on resolving that ordering, it requires an event-level independent pilot before acceptance.

## Optional independent path: Databento OPRA

Databento remains an optional verification provider for consolidated OPRA CBBO-1s or CMBP-1 observations. It is not required for the initial underlying study and no download is authorized.

The manual `.github/workflows/databento-cost-estimate.yml` workflow calls only `metadata.get_cost`, accepts no range over seven days, and records `download_performed: false`. A future pilot may proceed only after an explicit cost review and must never commit API keys or licensed data.

## Stage gates

1. Screen frozen entry families on SPY underlying minute bars.
2. Reject families that fail development or validation.
3. Replay surviving signals with QuantConnect option quote bars using ask entry, bid exit, costs, and adverse intrabar assumptions.
4. Use an optional higher-resolution OPRA pilot only if minute ambiguity materially changes the decision.
5. Preserve 2025+ as untouched holdout until the complete option specification is frozen.

Failure at any gate stops the options path. A low-fidelity fill model is not an acceptable substitute.
