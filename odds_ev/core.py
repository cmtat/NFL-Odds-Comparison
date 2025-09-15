"""Core logic for odds comparison and expected value analysis."""
from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from dataclasses import dataclass
from io import BytesIO
from statistics import mean
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup

SHARP_BOOKS = {"pinnacle", "bookmaker", "circasports"}

try:
    from PIL import Image
except ImportError:  # pragma: no cover - pillow optional for screenshot parsing
    Image = None  # type: ignore

try:  # pragma: no cover - pytesseract optional for screenshot parsing
    import pytesseract
except ImportError:  # pragma: no cover
    pytesseract = None  # type: ignore


@dataclass
class UserLine:
    """Representation of a betting line from the user's sportsbook."""

    label: str
    odds: float
    point: Optional[float] = None
    raw_source: Optional[str] = None

    def as_tuple(self) -> Tuple[str, float]:
        return self.label, self.odds


def american_to_implied_prob(odds: float) -> float:
    """Convert American odds to implied probability."""
    if odds > 0:
        return 100.0 / (odds + 100.0)
    return -odds / (-odds + 100.0)


def american_to_decimal(odds: float) -> float:
    """Convert American odds to decimal format."""
    if odds > 0:
        return 1.0 + odds / 100.0
    return 1.0 + 100.0 / -odds


def probability_to_american(prob: float) -> float:
    """Convert a probability to American odds."""
    if prob <= 0 or prob >= 1:
        raise ValueError("Probability must be between 0 and 1 (exclusive)")
    if prob < 0.5:
        return round((100.0 * (1.0 - prob)) / prob, 0)
    return round(-100.0 * prob / (1.0 - prob), 0)


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


def kelly_fraction(true_prob: float, odds: float) -> float:
    """Fraction of bankroll suggested by the Kelly criterion."""
    decimal_odds = american_to_decimal(odds)
    b = decimal_odds - 1.0
    if b <= 0:
        return 0.0
    p = true_prob
    q = 1.0 - p
    fraction = (b * p - q) / b
    return max(0.0, fraction)


def _canonicalize_team(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def _parse_lines_from_json_text(text: str) -> List[UserLine]:
    data = json.loads(text)
    if isinstance(data, dict) and "lines" in data:
        lines_field = data["lines"]
    elif isinstance(data, list):
        lines_field = data
    else:
        raise ValueError("JSON must contain a top-level 'lines' array")

    user_lines: List[UserLine] = []
    for entry in lines_field:
        if not isinstance(entry, dict):
            continue
        label = (
            entry.get("label")
            or entry.get("team")
            or entry.get("selection")
            or entry.get("name")
        )
        odds = entry.get("odds")
        if label is None or odds is None:
            continue
        point = entry.get("point")
        try:
            odds_value = float(odds)
        except (TypeError, ValueError):
            continue
        user_lines.append(UserLine(label=str(label), odds=odds_value, point=_coerce_point(point)))
    if not user_lines:
        raise ValueError("No lines were found in the JSON data")
    return user_lines


def _coerce_point(value: object) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_lines_from_html_text(text: str) -> List[UserLine]:
    soup = BeautifulSoup(text, "html.parser")
    lines: List[UserLine] = []
    for node in soup.select("[data-odds]"):
        label = (
            node.get("data-team")
            or node.get("data-selection")
            or node.get("data-name")
            or node.get("aria-label")
            or node.text.strip()
        )
        odds = node.get("data-odds")
        if not label or odds is None:
            continue
        try:
            odds_value = float(odds)
        except ValueError:
            continue
        point = node.get("data-point")
        point_value = _coerce_point(point)
        lines.append(UserLine(label=label.strip(), odds=odds_value, point=point_value))
    if not lines:
        raise ValueError(
            "No odds were detected. Ensure the HTML contains data-odds attributes."
        )
    return lines


def _parse_lines_from_text(text: str) -> List[UserLine]:
    pattern = re.compile(r"([A-Za-z0-9 .&'/-]{3,}?)\s*([+-]\d{2,4})")
    lines: List[UserLine] = []
    for raw_line in text.splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        matches = list(pattern.finditer(raw_line))
        for match in matches:
            label = match.group(1).strip()
            odds_str = match.group(2)
            try:
                odds_value = float(odds_str)
            except ValueError:
                continue
            if len(label) <= 2:
                continue
            lines.append(UserLine(label=label, odds=odds_value, raw_source=raw_line))
    # Remove potential duplicates while preserving order
    unique: Dict[Tuple[str, float], UserLine] = {}
    for line in lines:
        key = (line.label.lower(), line.odds)
        if key not in unique:
            unique[key] = line
    if not unique:
        raise ValueError("Unable to extract odds from the provided text")
    return list(unique.values())


def parse_lines_from_image_bytes(data: bytes) -> Tuple[List[UserLine], str]:
    if Image is None or pytesseract is None:
        raise RuntimeError(
            "Screenshot parsing requires Pillow and pytesseract with the Tesseract OCR binary installed."
        )
    with Image.open(BytesIO(data)) as img:
        grayscale = img.convert("L")
        text = pytesseract.image_to_string(grayscale)
    lines = _parse_lines_from_text(text)
    return lines, text


def parse_lines_from_path(path: str) -> List[UserLine]:
    ext = os.path.splitext(path)[1].lower()
    with open(path, "rb") as fh:
        data = fh.read()
    return parse_lines_from_bytes(data, ext)


def parse_lines_from_bytes(data: bytes, extension: str) -> List[UserLine]:
    extension = extension.lower()
    if extension == ".json":
        return _parse_lines_from_json_text(data.decode("utf-8"))
    if extension in {".html", ".htm"}:
        return _parse_lines_from_html_text(data.decode("utf-8", errors="ignore"))
    if extension in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
        lines, _ = parse_lines_from_image_bytes(data)
        return lines
    raise ValueError("Unsupported file format. Use JSON, HTML, or an image screenshot.")


def parse_lines_from_upload(filename: str, data: bytes) -> Tuple[List[UserLine], Optional[str]]:
    extension = os.path.splitext(filename)[1].lower()
    if extension in {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}:
        lines, text = parse_lines_from_image_bytes(data)
        return lines, text
    lines = parse_lines_from_bytes(data, extension)
    return lines, None


def fetch_sports(api_key: str) -> List[Dict[str, str]]:
    url = "https://api.the-odds-api.com/v4/sports/"
    params = {"apiKey": api_key}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    sports = resp.json()
    if not isinstance(sports, list):
        raise RuntimeError("Unexpected response when fetching sports list")
    return sports


def fetch_events(api_key: str, sport: str) -> List[Dict[str, object]]:
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/events/"
    params = {"apiKey": api_key}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    events = resp.json()
    if not isinstance(events, list):
        raise RuntimeError("Unexpected response when fetching events")
    return events


def fetch_event_with_market(
    api_key: str, sport: str, event_id: str, market: str
) -> Dict[str, object]:
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
        raise RuntimeError("Event not found or no odds available")
    return events[0]


def determine_outcome_order(
    event: Dict[str, object], market: str, outcome_names: Iterable[str]
) -> List[str]:
    names = list(outcome_names)
    if not names:
        return []
    if market == "totals":
        preferred = []
        for key in ("over", "under"):
            for name in names:
                if name.lower().startswith(key):
                    preferred.append(name)
                    break
        for name in names:
            if name not in preferred:
                preferred.append(name)
        return preferred[:2]
    # spreads/h2h use team names; rely on home/away ordering
    order: List[str] = []
    for team_key in ("away_team", "home_team"):
        team = event.get(team_key)
        if not isinstance(team, str):
            continue
        canonical_team = _canonicalize_team(team)
        for name in names:
            if _canonicalize_team(name) == canonical_team and name not in order:
                order.append(name)
                break
    for name in names:
        if name not in order:
            order.append(name)
    return order[:2]


def compute_sharp_consensus(
    event: Dict[str, object], market: str
) -> Dict[str, object]:
    bookmakers = event.get("bookmakers", [])
    if not isinstance(bookmakers, list):
        raise RuntimeError("Unexpected event format from API")

    market_list: List[Dict[str, object]] = []
    sharp_markets: List[Dict[str, object]] = []
    for bookmaker in bookmakers:
        market_data = None
        for m in bookmaker.get("markets", []) or []:
            if m.get("key") == market:
                market_data = m
                break
        if not market_data:
            continue
        entry = {
            "bookmaker": bookmaker,
            "market": market_data,
        }
        market_list.append(entry)
        if bookmaker.get("key") in SHARP_BOOKS:
            sharp_markets.append(entry)

    if not sharp_markets:
        raise RuntimeError("No sharp bookmaker data available for this event")

    consensus_point: Optional[float] = None
    if market in {"spreads", "totals"}:
        point_counts: Counter[float] = Counter()
        for entry in sharp_markets:
            outcomes = entry["market"].get("outcomes", []) or []
            if not outcomes:
                continue
            point = outcomes[0].get("point")
            if isinstance(point, (int, float)):
                # Round to avoid floating precision inconsistencies
                point_counts[round(float(point), 2)] += 1
        if point_counts:
            consensus_point = point_counts.most_common(1)[0][0]

    outcome_prices: Dict[str, List[float]] = {}
    outcome_points: Dict[str, List[float]] = {}

    def include_entry(entry: Dict[str, object]) -> bool:
        if consensus_point is None:
            return True
        outcomes = entry["market"].get("outcomes", []) or []
        if not outcomes:
            return False
        point = outcomes[0].get("point")
        if point is None:
            return False
        return math.isclose(float(point), float(consensus_point), abs_tol=0.05)

    filtered_entries = [entry for entry in sharp_markets if include_entry(entry)]
    if not filtered_entries:
        filtered_entries = sharp_markets

    for entry in filtered_entries:
        outcomes = entry["market"].get("outcomes", []) or []
        for outcome in outcomes:
            name = str(outcome.get("name"))
            price = outcome.get("price")
            if price is None:
                continue
            try:
                price_value = float(price)
            except (TypeError, ValueError):
                continue
            outcome_prices.setdefault(name, []).append(price_value)
            point_val = outcome.get("point")
            if isinstance(point_val, (int, float)):
                outcome_points.setdefault(name, []).append(float(point_val))

    if len(outcome_prices) < 2:
        raise RuntimeError("Not enough outcome data to compute consensus")

    order = determine_outcome_order(event, market, outcome_prices.keys())
    if len(order) < 2:
        order = list(outcome_prices.keys())[:2]

    consensus_outcomes: List[Dict[str, object]] = []
    avg_prices: List[float] = []
    for name in order[:2]:
        prices = outcome_prices.get(name, [])
        if not prices:
            continue
        avg_price = mean(prices)
        avg_prices.append(avg_price)
        points = outcome_points.get(name, [])
        point_value = mean(points) if points else consensus_point
        consensus_outcomes.append(
            {
                "name": name,
                "avg_price": avg_price,
                "point": point_value,
            }
        )

    if len(consensus_outcomes) < 2:
        raise RuntimeError("Insufficient data after computing consensus outcomes")

    prob_a, prob_b = vig_free_probabilities(avg_prices[0], avg_prices[1])
    for outcome, prob in zip(consensus_outcomes, (prob_a, prob_b)):
        outcome["true_prob"] = prob
        try:
            outcome["fair_price"] = probability_to_american(prob)
        except ValueError:
            outcome["fair_price"] = None

    return {
        "market": market,
        "outcomes": consensus_outcomes,
        "consensus_point": consensus_point,
        "bookmakers": market_list,
    }


def match_line_to_outcome(
    line: UserLine, outcomes: Sequence[Dict[str, object]], market: str
) -> Tuple[Optional[Dict[str, object]], str]:
    if market == "totals":
        label = line.label.lower()
        if "over" in label:
            for outcome in outcomes:
                if outcome["name"].lower().startswith("over"):
                    return outcome, "matched by keyword"
        if "under" in label:
            for outcome in outcomes:
                if outcome["name"].lower().startswith("under"):
                    return outcome, "matched by keyword"
    canonical_label = _canonicalize_team(line.label)
    if canonical_label:
        for outcome in outcomes:
            if _canonicalize_team(str(outcome["name"])) == canonical_label:
                return outcome, "matched by name"
        for outcome in outcomes:
            if canonical_label in _canonicalize_team(str(outcome["name"])):
                return outcome, "matched by partial name"
    return None, "no match"


def analyze_user_lines(
    lines: Sequence[UserLine],
    consensus: Dict[str, object],
    stake: float,
    bankroll: float,
    fractional_kelly: float,
) -> Tuple[List[Dict[str, object]], List[str]]:
    outcomes = list(consensus.get("outcomes", []))
    market = str(consensus.get("market", ""))
    consensus_point = consensus.get("consensus_point")
    used_outcomes: set[str] = set()
    results: List[Dict[str, object]] = []
    warnings: List[str] = []

    for idx, line in enumerate(lines):
        outcome, reason = match_line_to_outcome(line, outcomes, market)
        if outcome and outcome["name"] in used_outcomes:
            outcome = None
            reason = "outcome already matched"
        if outcome is None:
            # Fallback: assign next available outcome to keep flow
            remaining = [o for o in outcomes if o["name"] not in used_outcomes]
            if len(remaining) == 1 and len(lines) == 2:
                outcome = remaining[0]
                reason = "assigned remaining outcome"
        if outcome is None:
            warnings.append(
                f"Could not match '{line.label}' to a market outcome; please adjust the label."
            )
            results.append(
                {
                    "label": line.label,
                    "odds": line.odds,
                    "status": "unmatched",
                    "message": reason,
                }
            )
            continue

        used_outcomes.add(outcome["name"])
        true_prob = float(outcome.get("true_prob", 0.0))
        fair_price = outcome.get("fair_price")
        ev = expected_value(true_prob, line.odds, stake)
        base_kelly = kelly_fraction(true_prob, line.odds)
        recommended_fraction = max(0.0, base_kelly * max(0.0, fractional_kelly))
        recommended_bet = bankroll * recommended_fraction
        result = {
            "label": line.label,
            "odds": line.odds,
            "status": "matched",
            "matched_outcome": outcome["name"],
            "true_prob": true_prob,
            "fair_price": fair_price,
            "expected_value": ev,
            "kelly_fraction": base_kelly,
            "recommended_fraction": recommended_fraction,
            "recommended_bet": recommended_bet,
            "consensus_price": outcome.get("avg_price"),
            "consensus_point": consensus_point,
            "match_reason": reason,
        }
        if line.point is not None:
            result["user_point"] = line.point
            if consensus_point is not None and not math.isclose(
                float(line.point), float(consensus_point), abs_tol=0.25
            ):
                warnings.append(
                    f"Line '{line.label}' uses point {line.point}, which differs from the consensus {consensus_point}."
                )
        results.append(result)

    results.sort(key=lambda item: item.get("expected_value", float("-inf")), reverse=True)
    return results, warnings
