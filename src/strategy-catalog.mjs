const deepFreeze = (value) => {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value)) deepFreeze(child);
  }
  return value;
};

export const ENTRY_STRATEGIES = deepFreeze([
  {
    id: "US_OPENING_DRIVE",
    name: "SPY Opening Drive Continuation",
    status: "CANDIDATE",
    paperEnabled: false,
    underlying: "SPY",
    observationWindowEt: { start: "09:30", end: "09:45" },
    signalWindowEt: { start: "09:45", end: "10:30" },
    direction: "BOTH",
    requiredFeatures: ["openingRange", "vwap", "relativeVolume", "realizedVolatility"],
    hypothesis: "An accepted break of the opening range with VWAP and participation confirmation continues.",
  },
  {
    id: "US_FAILED_OPEN_BREAK",
    name: "SPY Failed Opening Break Reversal",
    status: "CANDIDATE",
    paperEnabled: false,
    underlying: "SPY",
    observationWindowEt: { start: "09:30", end: "10:00" },
    signalWindowEt: { start: "09:45", end: "11:00" },
    direction: "BOTH",
    requiredFeatures: ["openingRange", "vwap", "rejectionClose", "relativeVolume"],
    hypothesis: "A failed opening-range break that closes back inside and reclaims VWAP reverses.",
  },
  {
    id: "US_MIDDAY_COMPRESSION",
    name: "SPY Midday Compression Breakout",
    status: "CANDIDATE",
    paperEnabled: false,
    underlying: "SPY",
    observationWindowEt: { start: "10:30", end: "12:30" },
    signalWindowEt: { start: "12:30", end: "14:00" },
    direction: "BOTH",
    requiredFeatures: ["rangeCompression", "vwap", "volumeExpansion", "morningRange"],
    hypothesis: "A low-volatility midday balance followed by renewed participation produces expansion.",
  },
  {
    id: "US_POWER_HOUR_MOMENTUM",
    name: "SPY Power-Hour Momentum",
    status: "CANDIDATE",
    paperEnabled: false,
    underlying: "SPY",
    observationWindowEt: { start: "09:30", end: "15:00" },
    signalWindowEt: { start: "15:00", end: "15:15" },
    direction: "BOTH",
    requiredFeatures: ["firstHalfHourReturn", "sessionReturn", "vwap", "relativeVolume", "realizedVolatility"],
    hypothesis: "A sufficiently strong, high-participation session trend persists into the final hour.",
  },
]);

export const EXIT_OVERLAYS = deepFreeze([
  {
    id: "STRUCTURAL_2R",
    name: "Underlying Structure Stop and 2R Target",
    kind: "STRUCTURAL",
    status: "PRIMARY_BENCHMARK",
    paperEnabled: false,
  },
  {
    id: "US_V2_LITERAL",
    name: "US $1.80 Momentum V2 Literal Port",
    kind: "PREMIUM_V2",
    status: "SECONDARY_BENCHMARK",
    paperEnabled: false,
    referencePremiumUsd: 1.8,
    initialStopUsd: 1.6,
    trailActivationUsd: 2.2,
    trailGapUsd: 0.2,
  },
  {
    id: "US_V3_005_LITERAL",
    name: "US $1.80 Stepped Trail V3 $0.05 Literal Port",
    kind: "PREMIUM_V3",
    status: "SECONDARY_BENCHMARK",
    paperEnabled: false,
    referencePremiumUsd: 1.8,
    initialStopUsd: 1.6,
    trailGapUsd: 0.2,
    trailStepUsd: 0.05,
  },
  {
    id: "US_V3_010_LITERAL",
    name: "US $1.80 Stepped Trail V3 $0.10 Literal Port",
    kind: "PREMIUM_V3",
    status: "SECONDARY_BENCHMARK",
    paperEnabled: false,
    referencePremiumUsd: 1.8,
    initialStopUsd: 1.6,
    trailGapUsd: 0.2,
    trailStepUsd: 0.1,
  },
]);

export function validateStrategyCatalog() {
  const ids = [...ENTRY_STRATEGIES, ...EXIT_OVERLAYS].map((item) => item.id);
  if (new Set(ids).size !== ids.length) throw new Error("strategy and overlay IDs must be unique");
  if (ENTRY_STRATEGIES.some((item) => item.paperEnabled)) throw new Error("candidate entries must not be paper-enabled");
  if (EXIT_OVERLAYS.some((item) => item.paperEnabled)) throw new Error("untested exits must not be paper-enabled");
  if (ENTRY_STRATEGIES.some((item) => item.underlying !== "SPY")) throw new Error("foundation candidates must remain SPY-only");
  return true;
}

export function exitOverlay(id) {
  return EXIT_OVERLAYS.find((item) => item.id === id) ?? null;
}
