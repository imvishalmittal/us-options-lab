import assert from "node:assert/strict";
import test from "node:test";

import { buildMinuteQuoteBars, quoteRejectionReason } from "../src/quote-bars.mjs";

test("builds causal bid and ask OHLC from ordered quote observations", () => {
  const { bars, rejections } = buildMinuteQuoteBars([
    { timestamp: "2026-01-02T14:35:20.000Z", optionSymbol: "SPY_TEST", bid: 1.79, ask: 1.82, bidSize: 10, askSize: 8 },
    { timestamp: "2026-01-02T14:35:05.000Z", optionSymbol: "SPY_TEST", bid: 1.77, ask: 1.8, bidSize: 5, askSize: 6 },
    { timestamp: "2026-01-02T14:35:50.000Z", optionSymbol: "SPY_TEST", bid: 1.76, ask: 1.79, bidSize: 7, askSize: 9 },
  ]);
  assert.equal(rejections.length, 0);
  assert.deepEqual(bars[0].bid, { open: 1.77, high: 1.79, low: 1.76, close: 1.76 });
  assert.deepEqual(bars[0].ask, { open: 1.8, high: 1.82, low: 1.79, close: 1.79 });
  assert.equal(bars[0].quoteCount, 3);
});

test("rejects crossed and zero-size quotes", () => {
  assert.equal(quoteRejectionReason({
    timestamp: "2026-01-02T14:35:00.000Z", optionSymbol: "SPY_TEST",
    bid: 1.83, ask: 1.82, bidSize: 1, askSize: 1,
  }), "CROSSED_MARKET");
  assert.equal(quoteRejectionReason({
    timestamp: "2026-01-02T14:35:00.000Z", optionSymbol: "SPY_TEST",
    bid: 1.8, ask: 1.82, bidSize: 0, askSize: 1,
  }), "ZERO_OR_MISSING_SIZE");
});
