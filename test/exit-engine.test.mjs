import assert from "node:assert/strict";
import test from "node:test";

import {
  createExitPosition,
  processCompletedBidBar,
  proposedPremiumStop,
} from "../src/exit-engine.mjs";
import { exitOverlay } from "../src/strategy-catalog.mjs";

const bar = (timestamp, open, high, low, close) => ({
  timestamp,
  bid: { open, high, low, close },
});

test("V2 does not trail before $2.20 and activates from the next completed bar", () => {
  let position = createExitPosition({
    entryUsd: 1.81,
    entryTime: "2026-01-02T14:46:00.000Z",
    overlay: exitOverlay("US_V2_LITERAL"),
  });
  position = processCompletedBidBar(position, bar("2026-01-02T14:47:00.000Z", 1.82, 2.19, 1.8, 2.18));
  assert.equal(position.activeStopUsd, 1.6);
  position = processCompletedBidBar(position, bar("2026-01-02T14:48:00.000Z", 2.18, 2.21, 2.1, 2.2));
  assert.equal(position.activeStopUsd, 2.01);
  assert.equal(position.exit, null);
  position = processCompletedBidBar(position, bar("2026-01-02T14:49:00.000Z", 2.08, 2.1, 2.0, 2.02));
  assert.equal(position.exit.fillUsd, 2.01);
  assert.equal(position.exit.result, "TRAIL_STOP");
});

test("V3 $0.05 ratchets sooner than V3 $0.10", () => {
  const entry = 1.81;
  const v305 = createExitPosition({
    entryUsd: entry,
    entryTime: "2026-01-02T14:46:00.000Z",
    overlay: exitOverlay("US_V3_005_LITERAL"),
  });
  const v310 = createExitPosition({
    entryUsd: entry,
    entryTime: "2026-01-02T14:46:00.000Z",
    overlay: exitOverlay("US_V3_010_LITERAL"),
  });
  const moved305 = processCompletedBidBar(v305, bar("2026-01-02T14:47:00.000Z", 1.82, 1.86, 1.8, 1.85));
  const moved310 = processCompletedBidBar(v310, bar("2026-01-02T14:47:00.000Z", 1.82, 1.86, 1.8, 1.85));
  assert.equal(moved305.activeStopUsd, 1.66);
  assert.equal(moved310.activeStopUsd, 1.6);
});

test("V3 stops reach entry after a $0.20 favorable move", () => {
  let position = createExitPosition({
    entryUsd: 1.81,
    entryTime: "2026-01-02T14:46:00.000Z",
    overlay: exitOverlay("US_V3_010_LITERAL"),
  });
  position.peakBidUsd = 2.01;
  assert.equal(proposedPremiumStop(position), 1.81);
});

test("a gap through the active stop fills at the lower bid open", () => {
  let position = createExitPosition({
    entryUsd: 1.81,
    entryTime: "2026-01-02T14:46:00.000Z",
    overlay: exitOverlay("US_V2_LITERAL"),
  });
  position.activeStopUsd = 1.72;
  position.trailActivated = true;
  position = processCompletedBidBar(position, bar("2026-01-02T14:47:00.000Z", 1.65, 1.7, 1.6, 1.68));
  assert.equal(position.exit.fillUsd, 1.65);
});
