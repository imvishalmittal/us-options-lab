#!/usr/bin/env python3
"""Estimate Databento OPRA historical-data cost without downloading data."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from typing import Any


DATASET = "OPRA.PILLAR"
ALLOWED_SCHEMAS = {"definition", "cbbo-1m", "cbbo-1s", "cmbp-1"}
ALLOWED_STYPES = {"parent", "raw_symbol"}
MAX_RANGE_SECONDS = 7 * 24 * 60 * 60
MAX_SYMBOLS = 25


def parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as error:
        raise ValueError(f"invalid ISO-8601 timestamp: {value}") from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamps must include a UTC offset or Z")
    return parsed


def build_request(
    *, start: str, end: str, schema: str, symbols: list[str], stype_in: str
) -> dict[str, Any]:
    if schema not in ALLOWED_SCHEMAS:
        raise ValueError(f"schema must be one of: {', '.join(sorted(ALLOWED_SCHEMAS))}")
    if stype_in not in ALLOWED_STYPES:
        raise ValueError(f"stype_in must be one of: {', '.join(sorted(ALLOWED_STYPES))}")
    if not symbols or len(symbols) > MAX_SYMBOLS:
        raise ValueError(f"provide between 1 and {MAX_SYMBOLS} symbols")

    start_time = parse_timestamp(start)
    end_time = parse_timestamp(end)
    duration = (end_time - start_time).total_seconds()
    if duration <= 0:
        raise ValueError("end must be later than start")
    if duration > MAX_RANGE_SECONDS:
        raise ValueError("cost-estimate range cannot exceed 7 days")

    return {
        "dataset": DATASET,
        "start": start,
        "end": end,
        "symbols": symbols,
        "schema": schema,
        "stype_in": stype_in,
    }


def estimate_cost(client: Any, request: dict[str, Any]) -> float:
    """Call only Databento's non-downloading metadata cost endpoint."""
    return float(client.metadata.get_cost(**request))


def create_client(api_key: str) -> Any:
    import databento as db

    return db.Historical(api_key)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="ISO-8601 timestamp with offset")
    parser.add_argument("--end", required=True, help="ISO-8601 timestamp with offset")
    parser.add_argument("--schema", choices=sorted(ALLOWED_SCHEMAS), default="cbbo-1s")
    parser.add_argument("--symbols", default="SPY.OPT", help="comma-separated symbols")
    parser.add_argument("--stype-in", choices=sorted(ALLOWED_STYPES), default="parent")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = os.environ.get("DATABENTO_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("DATABENTO_API_KEY is required; store it as a GitHub Actions secret")

    symbols = [symbol.strip() for symbol in args.symbols.split(",") if symbol.strip()]
    try:
        request = build_request(
            start=args.start,
            end=args.end,
            schema=args.schema,
            symbols=symbols,
            stype_in=args.stype_in,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    cost = estimate_cost(create_client(api_key), request)
    print(
        json.dumps(
            {
                "request": request,
                "estimated_cost_usd": round(cost, 6),
                "download_performed": False,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
