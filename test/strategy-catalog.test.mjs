import assert from "node:assert/strict";
import test from "node:test";

import {
  ENTRY_STRATEGIES,
  EXIT_OVERLAYS,
  exitOverlay,
  validateStrategyCatalog,
} from "../src/strategy-catalog.mjs";

test("catalog is valid and nothing is paper-enabled", () => {
  assert.equal(validateStrategyCatalog(), true);
  assert.equal(ENTRY_STRATEGIES.length, 4);
  assert.ok(ENTRY_STRATEGIES.every((item) => item.paperEnabled === false));
  assert.ok(EXIT_OVERLAYS.every((item) => item.paperEnabled === false));
});

test("US entries cover open, midday, and power hour", () => {
  assert.ok(ENTRY_STRATEGIES.some((item) => item.id === "US_OPENING_DRIVE"));
  assert.ok(ENTRY_STRATEGIES.some((item) => item.id === "US_MIDDAY_COMPRESSION"));
  assert.ok(ENTRY_STRATEGIES.some((item) => item.id === "US_POWER_HOUR_MOMENTUM"));
});

test("V2 and both V3 literal ports remain secondary benchmarks", () => {
  assert.equal(exitOverlay("US_V2_LITERAL").status, "SECONDARY_BENCHMARK");
  assert.equal(exitOverlay("US_V3_005_LITERAL").trailStepUsd, 0.05);
  assert.equal(exitOverlay("US_V3_010_LITERAL").trailStepUsd, 0.1);
});
