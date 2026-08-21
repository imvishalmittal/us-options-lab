const deepFreeze = (value) => {
  if (value && typeof value === "object" && !Object.isFrozen(value)) {
    Object.freeze(value);
    for (const child of Object.values(value)) {
      deepFreeze(child);
    }
  }
  return value;
};

export const RESEARCH_CONFIG = deepFreeze({
  mode: "RESEARCH_ONLY",
  liveOrdersEnabled: false,
  brokerIntegrationEnabled: false,
  paperAccount: {
    startingCapitalUsd: 1000,
    cashOnly: true,
    maximumConcurrentPositions: 1,
    maximumInitialDebitUsd: 220,
  },
  market: {
    timezone: "America/New_York",
    primaryUnderlying: "SPY",
    additionalUnderlyingsEnabled: false,
  },
  execution: {
    contractsPerSimulation: 1,
    allowShortOptions: false,
    allowSpreads: false,
    allowOvernightPositions: false,
    minimumDte: 1,
    entryWindowEt: {
      start: "09:35",
      end: "10:00",
    },
    forcedExitEt: "15:45",
    entryFill: "ASK",
    exitFill: "BID",
  },
  selectors: {
    fixedPremium: {
      enabled: true,
      targetPremiumUsd: 1.8,
      minimumPremiumUsd: 1.6,
      maximumPremiumUsd: 2.2,
    },
    deltaDebit: {
      enabled: true,
      minimumAbsoluteDelta: 0.35,
      maximumAbsoluteDelta: 0.45,
      maximumDebitUsd: 220,
    },
  },
  evidence: {
    requireOneMinuteUnderlyingBars: true,
    requireOneMinuteOptionQuotes: true,
    requireBidAskQuotes: true,
    requireExpiredContracts: true,
    requireFeesAndSlippage: true,
    rejectIncompleteSessions: true,
  },
});

const assert = (condition, message) => {
  if (!condition) throw new Error(message);
};

export function validateResearchConfig(config = RESEARCH_CONFIG) {
  assert(config.mode === "RESEARCH_ONLY", "mode must remain RESEARCH_ONLY");
  assert(config.liveOrdersEnabled === false, "live orders must remain disabled");
  assert(config.brokerIntegrationEnabled === false, "broker integration must remain disabled");
  assert(config.paperAccount.startingCapitalUsd === 1000, "paper starting capital must remain $1,000");
  assert(config.paperAccount.cashOnly === true, "paper account must remain cash-only");
  assert(config.paperAccount.maximumConcurrentPositions === 1, "only one paper position is allowed");
  assert(
    config.paperAccount.maximumInitialDebitUsd <= config.paperAccount.startingCapitalUsd,
    "initial debit cannot exceed paper capital",
  );
  assert(config.market.primaryUnderlying === "SPY", "the foundation phase is SPY-only");
  assert(config.market.additionalUnderlyingsEnabled === false, "additional underlyings are not enabled");
  assert(config.execution.contractsPerSimulation === 1, "simulate exactly one contract");
  assert(config.execution.allowShortOptions === false, "short options are prohibited");
  assert(config.execution.allowOvernightPositions === false, "overnight positions are prohibited");
  assert(config.execution.minimumDte >= 1, "0DTE is excluded from the foundation phase");
  assert(config.execution.entryFill === "ASK", "entries must be modeled at the ask");
  assert(config.execution.exitFill === "BID", "exits must be modeled at the bid");
  assert(config.evidence.requireBidAskQuotes === true, "bid/ask evidence is mandatory");
  assert(config.evidence.requireFeesAndSlippage === true, "cost modeling is mandatory");
  return true;
}
