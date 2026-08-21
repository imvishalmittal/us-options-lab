const minuteKey = (timestamp) => {
  const millis = Date.parse(timestamp);
  if (!Number.isFinite(millis)) return null;
  return new Date(Math.floor(millis / 60000) * 60000).toISOString();
};

export function quoteRejectionReason(quote) {
  if (!minuteKey(quote?.timestamp)) return "INVALID_TIMESTAMP";
  if (!quote?.optionSymbol || typeof quote.optionSymbol !== "string") return "MISSING_SYMBOL";
  if (!Number.isFinite(quote.bid) || !Number.isFinite(quote.ask) || quote.bid <= 0 || quote.ask <= 0) {
    return "INVALID_PRICE";
  }
  if (quote.bid > quote.ask) return "CROSSED_MARKET";
  if (!Number.isFinite(quote.bidSize) || !Number.isFinite(quote.askSize)
      || quote.bidSize <= 0 || quote.askSize <= 0) return "ZERO_OR_MISSING_SIZE";
  return null;
}

const updateOhlc = (ohlc, value) => ({
  open: ohlc?.open ?? value,
  high: Math.max(ohlc?.high ?? value, value),
  low: Math.min(ohlc?.low ?? value, value),
  close: value,
});

export function buildMinuteQuoteBars(quotes) {
  const rejections = [];
  const groups = new Map();
  const ordered = [...quotes].sort((a, b) => Date.parse(a.timestamp) - Date.parse(b.timestamp));

  for (const quote of ordered) {
    const reason = quoteRejectionReason(quote);
    if (reason) {
      rejections.push({ quote, reason });
      continue;
    }
    const timestamp = minuteKey(quote.timestamp);
    const key = `${quote.optionSymbol}|${timestamp}`;
    const current = groups.get(key) ?? {
      timestamp,
      optionSymbol: quote.optionSymbol,
      bid: null,
      ask: null,
      quoteCount: 0,
    };
    current.bid = updateOhlc(current.bid, quote.bid);
    current.ask = updateOhlc(current.ask, quote.ask);
    current.quoteCount += 1;
    groups.set(key, current);
  }

  return {
    bars: [...groups.values()].sort((a, b) =>
      a.timestamp.localeCompare(b.timestamp) || a.optionSymbol.localeCompare(b.optionSymbol)),
    rejections,
  };
}
