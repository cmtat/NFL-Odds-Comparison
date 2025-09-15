#!/usr/bin/env python3
"""Command line tool to analyze betting lines for expected value."""

from __future__ import annotations

import argparse
import os
from typing import Sequence

from odds_ev import (
    UserLine,
    analyze_user_lines,
    compute_sharp_consensus,
    fetch_event_with_market,
    parse_lines_from_path,
)


def summarize_results(lines: Sequence[UserLine], results: Sequence[dict]) -> None:
    line_lookup = {line.label: line for line in lines}
    for result in results:
        if result.get("status") != "matched":
            label = result.get("label", "(unknown)")
            message = result.get("message", "")
            print(f"{label}: could not evaluate ({message})")
            continue
        label = result["label"]
        odds = result["odds"]
        ev = result["expected_value"]
        true_prob = result.get("true_prob")
        fair_price = result.get("fair_price")
        details = [f"EV={ev:.2f}"]
        if true_prob is not None:
            details.append(f"true p={true_prob:.3f}")
        if fair_price is not None:
            details.append(f"fair odds={fair_price}")
        print(f"{label}: odds {odds} ({', '.join(details)})")
        line = line_lookup.get(label)
        if line and line.point is not None:
            print(f"    User point: {line.point}")


def analyze_file(
    file_path: str,
    api_key: str,
    sport: str,
    event_id: str,
    market: str = "spreads",
    stake: float = 100.0,
) -> None:
    lines = parse_lines_from_path(file_path)
    if len(lines) < 2:
        raise RuntimeError("Expected at least two lines in the input file")
    event = fetch_event_with_market(api_key, sport, event_id, market)
    consensus = compute_sharp_consensus(event, market)
    results, warnings = analyze_user_lines(lines[:2], consensus, stake, stake, 1.0)
    summarize_results(lines[:2], results)
    if warnings:
        print()
        for warning in warnings:
            print(f"Warning: {warning}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute expected value for your sportsbook odds",
    )
    parser.add_argument("file", help="Path to your sportsbook odds file (HTML/JSON/image)")
    parser.add_argument("--api-key", dest="api_key", help="The Odds API key")
    parser.add_argument("--sport", default="americanfootball_nfl", help="Sport key for the event")
    parser.add_argument("--event", required=True, help="Event identifier from The Odds API")
    parser.add_argument(
        "--market",
        choices=["h2h", "spreads", "totals"],
        default="spreads",
        help="Market to analyze",
    )
    parser.add_argument(
        "--stake",
        type=float,
        default=100.0,
        help="Stake amount used when computing expected value",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api_key = args.api_key or os.environ.get("THE_ODDS_API_KEY")
    if not api_key:
        raise SystemExit("Provide an API key via --api-key or THE_ODDS_API_KEY")
    analyze_file(args.file, api_key, args.sport, args.event, args.market, args.stake)


if __name__ == "__main__":
    main()
