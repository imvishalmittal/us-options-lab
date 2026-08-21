const roundPrice = (value) => Math.round((value + Number.EPSILON) * 100) / 100;

function assertPremiumOverlay(overlay) {
  if (!overlay || !["PREMIUM_V2", "PREMIUM_V3"].includes(overlay.kind)) {
    throw new Error("a V2 or V3 premium overlay is required");
  }
}

export function createExitPosition({ entryUsd, entryTime, overlay }) {
  assertPremiumOverlay(overlay);
  if (!Number.isFinite(entryUsd) || entryUsd <= overlay.initialStopUsd) {
    throw new Error("entry must be above the initial stop");
  }
  return {
    overlay,
    entryUsd: roundPrice(entryUsd),
    entryTime,
    initialStopUsd: overlay.initialStopUsd,
    activeStopUsd: overlay.initialStopUsd,
    peakBidUsd: roundPrice(entryUsd),
    trailActivated: false,
    lastProcessed: null,
    stopHistory: [{ effectiveFrom: entryTime, stopUsd: overlay.initialStopUsd, reason: "initial" }],
    exit: null,
  };
}

export function proposedPremiumStop(position) {
  const { overlay } = position;
  assertPremiumOverlay(overlay);
  if (overlay.kind === "PREMIUM_V2") {
    return position.peakBidUsd < overlay.trailActivationUsd
      ? position.initialStopUsd
      : roundPrice(Math.max(position.initialStopUsd, position.peakBidUsd - overlay.trailGapUsd));
  }
  const favorableMove = Math.max(0, position.peakBidUsd - position.entryUsd);
  const steps = Math.floor((favorableMove + 1e-9) / overlay.trailStepUsd);
  return steps < 1
    ? position.initialStopUsd
    : roundPrice(Math.max(
      position.initialStopUsd,
      position.entryUsd + steps * overlay.trailStepUsd - overlay.trailGapUsd,
    ));
}

function assertBidBar(bar) {
  for (const field of ["open", "high", "low", "close"]) {
    if (!Number.isFinite(bar?.bid?.[field]) || bar.bid[field] <= 0) {
      throw new Error(`invalid bid ${field}`);
    }
  }
  if (bar.bid.high < Math.max(bar.bid.open, bar.bid.close, bar.bid.low)
      || bar.bid.low > Math.min(bar.bid.open, bar.bid.close, bar.bid.high)) {
    throw new Error("invalid bid OHLC ordering");
  }
}

export function processCompletedBidBar(position, bar) {
  assertBidBar(bar);
  if (position.exit || position.lastProcessed === bar.timestamp) return position;
  const next = {
    ...position,
    stopHistory: [...position.stopHistory],
    lastProcessed: bar.timestamp,
  };

  if (bar.bid.low <= next.activeStopUsd) {
    const fillUsd = bar.bid.open <= next.activeStopUsd ? bar.bid.open : next.activeStopUsd;
    next.exit = {
      time: bar.timestamp,
      fillUsd: roundPrice(fillUsd),
      result: next.trailActivated ? "TRAIL_STOP" : "INITIAL_STOP",
    };
    return next;
  }

  next.peakBidUsd = roundPrice(Math.max(next.peakBidUsd, bar.bid.high));
  const proposed = proposedPremiumStop(next);
  if (proposed > next.activeStopUsd) {
    next.activeStopUsd = proposed;
    next.trailActivated = true;
    next.stopHistory.push({
      effectiveFrom: null,
      sourceBar: bar.timestamp,
      sourcePeakBidUsd: next.peakBidUsd,
      stopUsd: proposed,
      reason: next.overlay.kind === "PREMIUM_V2" ? "continuous-trailing" : "stepped-trailing",
    });
  }
  return next;
}

export function exitAtSessionBid(position, bar) {
  assertBidBar(bar);
  return position.exit ? position : {
    ...position,
    exit: {
      time: bar.timestamp,
      fillUsd: roundPrice(bar.bid.close),
      result: "SESSION_EXIT",
    },
  };
}
