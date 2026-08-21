import assert from "node:assert/strict";
import test from "node:test";

import { RESEARCH_CONFIG, validateResearchConfig } from "../src/research-config.mjs";

test("foundation config is valid", () => {
  assert.equal(validateResearchConfig(), true);
});

test("live trading and broker integration are disabled", () => {
  assert.equal(RESEARCH_CONFIG.mode, "RESEARCH_ONLY");
  assert.equal(RESEARCH_CONFIG.liveOrdersEnabled, false);
  assert.equal(RESEARCH_CONFIG.brokerIntegrationEnabled, false);
});

test("foundation phase is SPY-only and excludes 0DTE", () => {
  assert.equal(RESEARCH_CONFIG.market.primaryUnderlying, "SPY");
  assert.equal(RESEARCH_CONFIG.market.additionalUnderlyingsEnabled, false);
  assert.ok(RESEARCH_CONFIG.execution.minimumDte >= 1);
});

test("execution uses conservative observable quote sides", () => {
  assert.equal(RESEARCH_CONFIG.execution.entryFill, "ASK");
  assert.equal(RESEARCH_CONFIG.execution.exitFill, "BID");
  assert.equal(RESEARCH_CONFIG.evidence.requireBidAskQuotes, true);
});

test("validator rejects accidental live-order enablement", () => {
  const unsafe = structuredClone(RESEARCH_CONFIG);
  unsafe.liveOrdersEnabled = true;
  assert.throws(() => validateResearchConfig(unsafe), /live orders must remain disabled/);
});

test("validator rejects 0DTE", () => {
  const unsafe = structuredClone(RESEARCH_CONFIG);
  unsafe.execution.minimumDte = 0;
  assert.throws(() => validateResearchConfig(unsafe), /0DTE is excluded/);
});
