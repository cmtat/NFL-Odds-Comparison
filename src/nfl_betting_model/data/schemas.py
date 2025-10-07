"""Typed records describing the data ingested for modeling."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(slots=True)
class GameScheduleRecord:
    game_id: str
    season: int
    week: int
    game_type: str
    home_team: str
    away_team: str
    kickoff_time_utc: datetime
    stadium: Optional[str] = None
    surface: Optional[str] = None
    roof_type: Optional[str] = None
    spread_line: Optional[float] = None
    total_line: Optional[float] = None


@dataclass(slots=True)
class TeamStatRecord:
    game_id: str
    team: str
    season: int
    week: int
    epa_per_play: Optional[float] = None
    success_rate: Optional[float] = None
    yards_per_play: Optional[float] = None
    red_zone_success: Optional[float] = None
    turnover_epa: Optional[float] = None


@dataclass(slots=True)
class BettingLineSnapshot:
    game_id: str
    timestamp: datetime
    market: str  # e.g. h2h, spreads, totals
    bookmaker: str
    price: float
    point: Optional[float] = None


@dataclass(slots=True)
class InjuryReport:
    player_id: str
    team: str
    report_time: datetime
    status: str
    description: Optional[str] = None
    expected_return: Optional[datetime] = None


@dataclass(slots=True)
class WeatherObservation:
    game_id: str
    observation_time: datetime
    temperature_f: Optional[float]
    wind_mph: Optional[float]
    precipitation_in: Optional[float]
    humidity_pct: Optional[float]
