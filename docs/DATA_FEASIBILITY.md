# Historical Options Data Feasibility

Status as of 2026-08-21: **provisional go for a small paid-or-credit pilot; no full download authorized.**

## Required evidence

A credible SPY options replay needs instrument definitions plus time-ordered bid and ask observations. A single option OHLC series or one end-of-minute quote is insufficient to reconstruct V2/V3 peak, stop, and gap ordering.

The provider-neutral ingestion layer therefore accepts quote observations and constructs separate one-minute bid and ask OHLC bars. Crossed markets, missing prices, and zero-size quotes are rejected with reason codes.

## Preferred pilot: Databento OPRA

Databento's OPRA dataset provides consolidated US equity-option data. Its CBBO-1m schema supplies the final consolidated bid and offer at each minute, and instrument definitions identify contracts. CBBO-1m is useful for coverage checks but does not contain the within-minute high and low required for faithful V2/V3 trailing logic.

For the execution pilot, use CBBO-1s or CMBP-1 observations and derive minute bid/ask bars while preserving event order. Databento documents CBBO-1s and CMBP-1 history from March 2023, while CBBO-1m and other lower-granularity history extend further.

Databento supports pay-as-you-go historical requests and exposes `metadata.get_cost`, so cost must be estimated before every download. New-account credits may cover a limited feasibility sample, but no assumption about available credit should be built into the code.

Official references:

- [Databento options/OPRA coverage](https://databento.com/options)
- [CBBO and CMBP schema definitions](https://databento.com/docs/schemas-and-data-formats/cbbo)
- [Historical pricing and cost estimation](https://databento.com/pricing/)

## Alternatives

- Massive exposes per-contract historical quotes with bid, ask, sizes, and nanosecond timestamps; its bulk options quote history dates to March 2022. This is a credible fallback if plan access and per-contract extraction cost are preferable. [Massive historical options quotes](https://massive.com/docs/rest/options/quotes)
- ThetaData advertises historical OPRA trades, quotes, chain snapshots, and NBBO coverage. It is a second fallback, but the local-terminal workflow and subscription tier must be evaluated before integration. [ThetaData options data](https://www.thetadata.net/options-data)

## Pilot specification

The first data request must be deliberately small:

- Five non-consecutive regular SPY sessions across different volatility conditions
- SPY underlying one-minute bars
- Contract definitions for 1–7 DTE calls and puts
- Only the contract slice needed around the $1.60–$2.20 band and 0.35–0.45 absolute delta
- CBBO-1s or CMBP-1 for the selected contracts
- Cost estimate recorded before download
- No secrets or downloaded licensed data committed to Git

## Cost-estimate workflow

`.github/workflows/databento-cost-estimate.yml` is manual-only. It runs the official pinned Python client against `metadata.get_cost`, accepts no range longer than seven days, and never invokes `timeseries.get_range` or a batch download.

The initial estimate may use `SPY.OPT` with `stype_in=parent` to price the full parent-symbol request. Later estimates should use no more than 25 explicitly resolved raw contracts so the cost reflects the intended debit/delta slice. Every output declares `download_performed: false` and is retained as a workflow artifact for 30 days.

Required setup: add a repository Actions secret named `DATABENTO_API_KEY`. Do not expose the key as a workflow input or commit it.

## Acceptance gates

- At least 99% of expected regular-session minutes available for selected contracts
- Valid, non-crossed bid/ask observations with positive sizes
- Correct daylight-saving and early-close handling
- Deterministic contract identity and expiry metadata
- Reproducible minute bars from ordered observations
- Enough quote density to resolve stop and trail ordering
- Pilot cost acceptable before any larger request

Failure of these gates means no options backtest. The fallback is a SPY/QQQ cash-ETF research lab, not fabricated option fills.
