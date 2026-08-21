#!/usr/bin/env node
import { RESEARCH_CONFIG, validateResearchConfig } from "./research-config.mjs";

validateResearchConfig();

const summary = {
  status: "READY_FOR_DATA_FEASIBILITY",
  mode: RESEARCH_CONFIG.mode,
  underlying: RESEARCH_CONFIG.market.primaryUnderlying,
  paperStartingCapitalUsd: RESEARCH_CONFIG.paperAccount.startingCapitalUsd,
  maximumInitialDebitUsd: RESEARCH_CONFIG.paperAccount.maximumInitialDebitUsd,
  liveOrdersEnabled: RESEARCH_CONFIG.liveOrdersEnabled,
  brokerIntegrationEnabled: RESEARCH_CONFIG.brokerIntegrationEnabled,
  minimumDte: RESEARCH_CONFIG.execution.minimumDte,
  entryWindowEt: RESEARCH_CONFIG.execution.entryWindowEt,
  forcedExitEt: RESEARCH_CONFIG.execution.forcedExitEt,
  selectors: Object.keys(RESEARCH_CONFIG.selectors),
};

if (process.argv.includes("--json")) {
  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
} else {
  process.stdout.write(
    [
      "US Options Lab",
      `Status: ${summary.status}`,
      `Mode: ${summary.mode}`,
      `Underlying: ${summary.underlying}`,
      `Paper capital: $${summary.paperStartingCapitalUsd}`,
      `Maximum initial debit: $${summary.maximumInitialDebitUsd}`,
      "Live orders: disabled",
      "Next gate: verify historical one-minute option bid/ask coverage",
      "",
    ].join("\n"),
  );
}
