# Research Protocol

## Objective

Determine whether a systematic, long-premium SPY options strategy has positive out-of-sample expectancy after observable spreads, fees, and slippage. The project is a research and paper-simulation system only.

## Foundation universe

- Simulated starting capital: $1,000
- Account model: cash-only
- Maximum concurrent positions: one
- Maximum initial option debit: $220
- Primary underlying: SPY
- Direction: long call or long put
- Size: one simulated contract
- Expiry: at least one full day remaining; 0DTE excluded
- Session: US regular market hours in `America/New_York`
- Entry window: 09:35–10:00 ET
- Forced exit: 15:45 ET
- No overnight positions, option writing, spreads, assignment, or exercise

The $1,000 balance is an accounting baseline for backtests and future paper sessions. It is not broker funding and cannot place a live order. QQQ, XSP, SPX, and individual-stock options are outside the foundation phase and require separate predeclared studies.

## Contract-selection hypotheses

Two selectors will be compared without hindsight:

1. Fixed premium: closest eligible contract to $1.80, within $1.60–$2.20.
2. Delta/debit: absolute delta 0.35–0.45, with debit no greater than $220.

A selector must use only information observable before the simulated order.

## Execution model

- Buy at the contemporaneous ask.
- Sell at the contemporaneous bid.
- Add explicit commissions, regulatory fees, and predeclared slippage.
- Debit, costs, and realized P&L must update the single $1,000 paper ledger.
- Reject a contract whose initial debit exceeds available paper cash or $220.
- If a quote is crossed, stale, missing, or otherwise invalid, reject the observation.
- Never synthesize a tradable quote from option OHLC alone.
- When event ordering within a bar is ambiguous, use the adverse outcome or reject the trade.

## Required historical evidence

The first implementation gate is data feasibility, not strategy optimization. A source must provide:

- One-minute SPY bars
- One-minute expired-option bid and ask quotes
- Contract metadata, strikes, expirations, and call/put type
- Correct splits and corporate-action handling
- Regular-session timestamps with DST-safe conversion
- Enough uninterrupted history for development, validation, and untouched holdout periods

If reliable expired bid/ask history is unavailable or unaffordable, the options backtest stops. The fallback research track is the underlying SPY/QQQ ETFs, not a low-fidelity options backtest.

## Evaluation

Report at minimum:

- Trade count and no-trade sessions
- Net P&L and expectancy after all modeled costs
- Win rate, profit factor, maximum drawdown, and longest losing streak
- MFE/MAE
- Results by direction, DTE, entry-time band, weekday, volatility regime, and selector
- Concentration in the best day, month, and trade
- Data rejection counts and reasons
- Paper balance, deployed debit, and return on the $1,000 starting capital

Development, validation, and holdout results must remain separate. A result is not deployable merely because one period is profitable.

## Governance

- Predeclare each strategy version before running it on validation or holdout data.
- Never tune against the holdout period.
- Keep mutually exclusive simulations separate; never add their P&L as if concurrently traded.
- No broker credentials, order endpoints, or live-order code.
- Forward paper automation starts only after historical feasibility and backtest acceptance.
