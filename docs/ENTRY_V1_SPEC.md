# Frozen SPY Entry V1 Specification

Status: frozen before the first QuantConnect result is inspected.

## Purpose and periods

This stage screens entry logic on one-minute SPY underlying bars. It does not simulate option contracts or dollar P&L.

- Development: 2018-01-01 through 2022-12-31
- Validation: 2023-01-01 through 2024-12-31
- Untouched holdout: 2025 onward

The holdout is absent from executable parameters. Thresholds must not be changed after validation is viewed.

## Shared causal rules

- Regular session only, `America/New_York`.
- Opening range: exactly the 15 bars from 09:30 through 09:44.
- Eligible opening-range width: 0.15%–0.80% of the 09:30 open.
- A signal uses only completed bars; virtual entry is the next bar's open.
- One virtual trade per strategy per session.
- Structural initial stop and fixed 2R target.
- If stop and target occur in the same minute, the stop is assumed first.
- A gap through the stop exits at the worse opening price.
- Remaining positions exit 15 minutes before the exchange's actual close
  (15:45 ET on regular sessions and 12:45 ET on standard early-close sessions).
- Strategies are alternative simulations; their R must not be added as one account.

VWAP is calculated causally from completed one-minute typical price and volume.

## E1 — Opening Drive Continuation

Eligible from 09:45 through 10:30.

1. Require two consecutive closes at least 0.05% beyond the same opening-range edge.
2. Both closes must be on the matching side of session VWAP.
3. The second close's volume must be at least 1.25 times the median of the preceding ten completed one-minute bars.
4. Enter on the next minute's open.
5. For a long, stop at opening-range high minus 25% of range width; mirror for a short.
6. Target 2R from the actual entry.

The volume input is an intraday recent-volume confirmation, not a multi-day relative-volume statistic.

## E2 — Failed Opening Break Reversal

Eligible from 09:45 through 11:00.

1. Price must sweep at least 0.05% beyond an opening-range edge.
2. The sweep bar must close back inside the range and on the reversal side of VWAP.
3. The immediately following bar must close beyond the sweep bar's opposite extreme and remain on the reversal side of VWAP.
4. Enter on the next minute's open.
5. Stop at the sweep wick extreme.
6. Target 2R from the actual entry.

## Promotion rule

An entry family can proceed to option replay only if both development and validation have a non-trivial trade count, positive average R, profit factor above 1, tolerable drawdown, and no dependence on a few outliers. These are necessary filters, not proof of live profitability.

Midday Compression and Power-Hour Momentum remain deferred. US V2 and V3 remain option-premium exit overlays and are not part of this underlying-entry stage.
