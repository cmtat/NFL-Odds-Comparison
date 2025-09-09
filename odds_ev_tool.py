#!/usr/bin/env python3
"""Command line tool to analyze betting lines for expected value.

Given a file containing odds from your sportsbook (HTML or JSON) and an event
id, this script uses The Odds API to pull sharp-bookmaker lines, removes the
vig to estimate true probabilities, and computes the expected value for the
uploaded odds.

Usage:
    python odds_ev_tool.py /path/to/lines.json --event EVENT_ID --api-key KEY

The API key can also be supplied via the THE_ODDS_API_KEY environment variable.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from typing import Iterable, List, Tuple

import requests
from bs4 import BeautifulSoup

SHARP_BOOKS = {"pinnacle", "bookmaker", "circasports"}


def american_to_implied_prob(odds: float) -> float:
    """Convert American odds to an implied probability."""
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return -odds / (-odds + 100.0)


def vig_free_probabilities(price_a: float, price_b: float) -> Tuple[float, float]:
    """Return vig-free probabilities for two outcomes."""
    p_a = american_to_implied_prob(price_a)
    p_b = american_to_implied_prob(price_b)
    total = p_a + p_b
    return p_a / total, p_b / total


def expected_value(true_prob: float, odds: float, stake: float) -> float:
    """Expected value of a bet with a given true probability and odds."""
    if odds > 0:
        profit = stake * (odds / 100.0)
    else:
        profit = stake * (100.0 / -odds)
    return true_prob * profit - (1 - true_prob) * stake


def parse_book_file(path: str) -> List[Tuple[str, float]]:
    """Parse a JSON or HTML file containing sportsbook odds.

    JSON format example::
        {
            "lines": [
                {"team": "Team A", "odds": -105},
                {"team": "Team B", "odds": 115}
            ]
        }

    HTML format example (attributes on any element)::
        <div data-team="Team A" data-odds="-105"></div>
        <div data-team="Team B" data-odds="115"></div>
    """

    if path.endswith(".json"):
        with open(path) as f:
            data = json.load(f)
        return [(line["team"], float(line["odds"])) for line in data["lines"]]

    if path.endswith(".html"):
        with open(path) as f:
            soup = BeautifulSoup(f, "html.parser")
        lines: List[Tuple[str, float]] = []
        for node in soup.select("[data-team][data-odds]"):
            lines.append((node["data-team"], float(node["data-odds"])))
        return lines

    raise ValueError("Unsupported file format: expected .json or .html")


def fetch_sharp_consensus(
    api_key: str, sport: str, event_id: str, market: str
) -> Tuple[float, float]:
    """Fetch average odds from sharp books for an event and market."""
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
    params = {
        "apiKey": api_key,
        "regions": "us",
        "markets": market,
        "eventIds": event_id,
        "oddsFormat": "american",
    }
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    events = resp.json()
    if not events:
        raise RuntimeError("Event not found")
    event = events[0]

    markets = []
    for bookmaker in event.get("bookmakers", []):
        if bookmaker.get("key") in SHARP_BOOKS:
            for m in bookmaker.get("markets", []):
                if m.get("key") == market:
                    markets.append(m)

    if not markets:
        raise RuntimeError("No sharp bookmaker data available for this event")

    # Determine consensus: most common line (point) if available, then average prices.
    prices: List[Tuple[float, float]] = []
    if market in {"spreads", "totals"}:
        points = [m["outcomes"][0]["point"] for m in markets]
        point_counts = Counter(points)
        consensus_point, _ = point_counts.most_common(1)[0]
        for m in markets:
            if m["outcomes"][0]["point"] == consensus_point:
                prices.append(
                    (m["outcomes"][0]["price"], m["outcomes"][1]["price"])
                )
    else:  # h2h
        for m in markets:
            prices.append((m["outcomes"][0]["price"], m["outcomes"][1]["price"]))

    avg_a = sum(p[0] for p in prices) / len(prices)
    avg_b = sum(p[1] for p in prices) / len(prices)
    return avg_a, avg_b


def analyze_file(
    file_path: str,
    api_key: str,
    sport: str,
    event_id: str,
    market: str = "spreads",
    stake: float = 100.0,
) -> None:
    lines = parse_book_file(file_path)
    if len(lines) != 2:
        raise RuntimeError("Expected exactly two lines in the input file")

    consensus_a, consensus_b = fetch_sharp_consensus(api_key, sport, event_id, market)
    prob_a, prob_b = vig_free_probabilities(consensus_a, consensus_b)

    for (team, odds), prob in zip(lines, (prob_a, prob_b)):
        ev = expected_value(prob, odds, stake)
        print(f"{team}: odds {odds}, EV={ev:.2f}")


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Analyze sportsbook odds for EV")
    parser.add_argument("file", help="Path to sportsbook odds file (.json or .html)")
    parser.add_argument("--event", required=True, help="Event ID to analyze")
    parser.add_argument("--api-key", default=os.getenv("THE_ODDS_API_KEY"))
    parser.add_argument(
        "--sport",
        default="americanfootball_nfl",
        help="Sport key, e.g. americanfootball_nfl",
    )
    parser.add_argument(
        "--market", default="spreads", help="Market type: spreads, h2h or totals"
    )
    parser.add_argument("--stake", type=float, default=100.0, help="Bet amount")

    args = parser.parse_args(list(argv) if argv is not None else None)

    if not args.api_key:
        raise SystemExit("API key required. Use --api-key or THE_ODDS_API_KEY env var")

    analyze_file(
        args.file,
        api_key=args.api_key,
        sport=args.sport,
        event_id=args.event,
        market=args.market,
        stake=args.stake,
    )


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main()
