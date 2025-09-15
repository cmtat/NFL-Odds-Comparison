"""Flask web application for sportsbook odds comparison and EV analysis."""
from __future__ import annotations

import os
from typing import List, Optional, Sequence, Tuple

from flask import Flask, flash, jsonify, render_template, request

from odds_ev import (
    SHARP_BOOKS,
    UserLine,
    analyze_user_lines,
    compute_sharp_consensus,
    fetch_event_with_market,
    fetch_events,
    fetch_sports,
    parse_lines_from_upload,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")

DEFAULT_SPORT_OPTIONS = [
    {"key": "americanfootball_nfl", "title": "American Football (NFL)"},
    {"key": "basketball_nba", "title": "Basketball (NBA)"},
    {"key": "baseball_mlb", "title": "Baseball (MLB)"},
]


def parse_manual_lines(form) -> Tuple[List[UserLine], List[str]]:
    names = form.getlist("line_name[]")
    odds_values = form.getlist("line_odds[]")
    points = form.getlist("line_point[]")
    errors: List[str] = []
    lines: List[UserLine] = []
    for idx, (name, odds_str, point_str) in enumerate(zip(names, odds_values, points)):
        name = (name or "").strip()
        odds_str = (odds_str or "").strip()
        point_str = (point_str or "").strip()
        if not name and not odds_str and not point_str:
            continue
        if not name or not odds_str:
            errors.append(f"Line {idx + 1}: provide both a label and odds value.")
            continue
        try:
            odds = float(odds_str)
        except ValueError:
            errors.append(f"Line {idx + 1}: invalid odds '{odds_str}'.")
            continue
        point: Optional[float] = None
        if point_str:
            try:
                point = float(point_str)
            except ValueError:
                errors.append(f"Line {idx + 1}: invalid point '{point_str}'.")
        lines.append(UserLine(label=name, odds=odds, point=point))
    return lines, errors


def prepare_line_inputs(lines: Sequence[UserLine]) -> List[dict]:
    return [
        {"label": line.label, "odds": line.odds, "point": line.point if line.point is not None else ""}
        for line in lines
    ]


def parse_float(value: Optional[str], default: float) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except ValueError:
        return default


@app.route("/events", methods=["POST"])
def list_events():
    payload = request.get_json(silent=True) or {}
    api_key = (payload.get("api_key") or "").strip()
    sport = (payload.get("sport") or "").strip()
    if not api_key or not sport:
        return jsonify({"events": [], "error": "API key and sport are required"}), 400
    try:
        events = fetch_events(api_key, sport)
    except Exception as exc:  # pragma: no cover - API failure path
        return jsonify({"events": [], "error": str(exc)}), 500
    event_options = [
        {
            "id": event.get("id"),
            "name": event.get("name"),
            "commence_time": event.get("commence_time"),
        }
        for event in events
    ]
    return jsonify({"events": event_options})


@app.route("/", methods=["GET", "POST"])
def index():
    api_key = (request.form.get("api_key") or os.environ.get("THE_ODDS_API_KEY") or "").strip()
    sport = request.form.get("sport") or "americanfootball_nfl"
    event_id = request.form.get("event_id") or ""
    market = request.form.get("market") or "spreads"
    stake = parse_float(request.form.get("stake"), 100.0)
    bankroll = parse_float(request.form.get("bankroll"), 1000.0)
    fractional_kelly = parse_float(request.form.get("fractional_kelly"), 1.0)
    fractional_kelly = max(0.0, min(fractional_kelly, 1.0))

    sports: List[dict] = []
    if api_key:
        try:
            sports = fetch_sports(api_key)
        except Exception as exc:
            flash(f"Unable to load sports list: {exc}", "warning")
    if not sports:
        sports = DEFAULT_SPORT_OPTIONS

    events = []
    if api_key and sport:
        try:
            events = fetch_events(api_key, sport)
        except Exception as exc:
            flash(f"Unable to load events for {sport}: {exc}", "warning")

    manual_lines, manual_errors = parse_manual_lines(request.form)
    for error in manual_errors:
        flash(error, "warning")

    upload_lines: List[UserLine] = []
    recognized_text: Optional[str] = None

    analysis_results = []
    analysis_warnings: List[str] = []
    consensus_data = None
    event_info = None
    bookmaker_rows = []

    if request.method == "POST":
        if manual_lines:
            lines_to_use = manual_lines
        else:
            upload = request.files.get("lines_file")
            if upload and upload.filename:
                data = upload.read()
                try:
                    upload_lines, recognized_text = parse_lines_from_upload(upload.filename, data)
                except Exception as exc:
                    flash(f"Could not parse uploaded file: {exc}", "danger")
                    upload_lines = []
                lines_to_use = upload_lines
            else:
                lines_to_use = []

        if not lines_to_use:
            flash("Provide odds either by uploading a file or entering them manually.", "danger")
        elif not api_key:
            flash("Enter your The Odds API key to analyze odds.", "danger")
        elif not event_id:
            flash("Select an event to analyze.", "danger")
        else:
            try:
                event_info = fetch_event_with_market(api_key, sport, event_id, market)
                consensus_data = compute_sharp_consensus(event_info, market)
                analysis_results, analysis_warnings = analyze_user_lines(
                    lines_to_use,
                    consensus_data,
                    stake=stake,
                    bankroll=bankroll,
                    fractional_kelly=fractional_kelly,
                )
            except Exception as exc:
                flash(f"Unable to analyze odds: {exc}", "danger")
            else:
                for warning in analysis_warnings:
                    flash(warning, "warning")
                bookmaker_rows = build_bookmaker_rows(consensus_data)

    if manual_lines:
        line_inputs = prepare_line_inputs(manual_lines)
    elif upload_lines:
        line_inputs = prepare_line_inputs(upload_lines)
    else:
        line_inputs = []

    if not line_inputs:
        line_inputs = [{"label": "", "odds": "", "point": ""} for _ in range(2)]

    return render_template(
        "index.html",
        api_key=api_key,
        sport=sport,
        sports=sports,
        events=events,
        event_id=event_id,
        market=market,
        stake=stake,
        bankroll=bankroll,
        fractional_kelly=fractional_kelly,
        line_inputs=line_inputs,
        recognized_text=recognized_text,
        analysis_results=analysis_results,
        consensus=consensus_data,
        bookmaker_rows=bookmaker_rows,
        event_info=event_info,
    )


def build_bookmaker_rows(consensus: Optional[dict]) -> List[dict]:
    if not consensus:
        return []
    outcomes = consensus.get("outcomes", []) or []
    outcome_names = [str(outcome.get("name")) for outcome in outcomes]
    rows: List[dict] = []
    for entry in consensus.get("bookmakers", []) or []:
        bookmaker = entry.get("bookmaker", {}) or {}
        market = entry.get("market", {}) or {}
        outcome_values = []
        available_outcomes = market.get("outcomes", []) or []
        for name in outcome_names:
            match = next((o for o in available_outcomes if o.get("name") == name), None)
            if match:
                outcome_values.append(
                    {
                        "price": match.get("price"),
                        "point": match.get("point"),
                    }
                )
            else:
                outcome_values.append({"price": None, "point": None})
        rows.append(
            {
                "title": bookmaker.get("title") or bookmaker.get("key"),
                "key": bookmaker.get("key"),
                "is_sharp": bookmaker.get("key") in SHARP_BOOKS,
                "last_update": market.get("last_update"),
                "outcomes": outcome_values,
            }
        )
    return rows


if __name__ == "__main__":  # pragma: no cover - manual launch
    app.run(debug=True)
