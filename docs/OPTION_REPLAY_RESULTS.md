# SPY option replay results

Status: **all tested option candidates rejected; no forward paper strategy authorized.**

All runs were order-free QuantConnect Cloud replays using one-minute SPY and
option quote bars. Entries use the next minute's ask plus $0.01 slippage; exits
use the bid less $0.01; commissions are $0.65 per side. Each variant is a
separate $1,000 ledger and results are never added as if they were one account.

## Underlying gate

`US_OPENING_DRIVE` passed the underlying screen before option replay:

| Period | Trades | Average R | Total R | Profit factor |
|---|---:|---:|---:|---:|
| 2018–2022 development | 766 | +0.106 | +81.55 | 1.17 |
| 2023–2024 validation | 302 | +0.088 | +26.71 | 1.14 |

`US_FAILED_OPEN_BREAK` was rejected in development and did not proceed.

## Literal translation baseline

Contract selector: nearest 1–7 DTE weekly contract with ask $1.60–$2.20,
spread no more than $0.20/15%, and absolute delta 0.35–0.45. The table combines
the five chronological development-year ledgers.

| Exit | Trades | Net P/L | Average/trade | Profit factor | Decision |
|---|---:|---:|---:|---:|---|
| Underlying structural 2R | 405 | **−$3,048.50** | −$7.53 | 0.72 | Reject |
| Literal V2 | 405 | **−$3,257.50** | −$8.04 | 0.48 | Reject |
| Literal V3, $0.05 step | 405 | **−$2,951.50** | −$7.29 | 0.41 | Reject |
| Literal V3, $0.10 step | 405 | **−$3,024.50** | −$7.47 | 0.44 | Reject |

QuantConnect algorithm IDs by year:

- 2018: `0107cce3afd3fae6a915aeac7c93005b`
- 2019: `49bdcdce864a7606859bd934e6d20b37`
- 2020: `a9837c4f6109c6fb011f84e65224c001`
- 2021 corrected early-close replay: `f38d5b3198be9e5bc08d6fd454597589`
- 2022: `a44cec7c8de504113748333721c674c9`

The first fixed-$1.80 selector development year was also decisive. In 2018 it
entered 124 cohorts and exhausted the $1,000 ledger in every exit variant;
structural P/L was −$888.20 and literal V2 was −$1,243.20. Algorithm ID:
`a1f6cf30286d2afa82ae8f1a7c7902b4`.

## US-balanced candidate

This independently frozen candidate used 5–10 DTE, preferred approximately
7 DTE, targeted absolute delta 0.30 within 0.20–0.35, and retained the
$1.60–$2.20 debit/spread gates.

| Development year | Structural trades | Structural net P/L | Profit factor |
|---|---:|---:|---:|
| 2018 | 42 | +$29.40 | 1.04 |
| 2019 | 34 | +$48.80 | 1.09 |
| 2020 | 117 | **−$155.10** | 0.92 |
| Combined | 193 | **−$76.90** | 0.98 |

The selector plus structural exit was rejected when it failed the predeclared
2020 stress gate. The entry-scaled 25%-risk/2R exit and +30%/15% trail were
already rejected after losing $309.60 and $475.60 respectively in 2018.

Algorithm IDs: 2018 `b24032dd60a527bbf977a9cc2d77754d`, 2019
`ea4e8479cabc3aded78262357a49d57b`, and 2020
`a9a118aa9578c97146e812a38b6c2aa6`.

## Research decision

- Do not paper-enable any option candidate.
- Do not run the failed candidates on validation or the 2025+ holdout.
- Treat January 2024 as a diagnostic feasibility slice, not pristine
  validation, because it was inspected while designing the replay.
- Preserve 2023 and 2025+ for a materially new, fully frozen hypothesis.
- Prefer a separate cash-SPY/QQQ study next; any future options study must
  change the economic structure, not merely tune these thresholds.

