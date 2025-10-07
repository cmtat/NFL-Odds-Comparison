"""Metadata describing each external data source."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional


@dataclass(frozen=True, slots=True)
class DataSource:
    name: str
    provider: str
    description: str
    update_frequency: timedelta
    retention_notes: Optional[str] = None
    coverage_start: Optional[int] = None  # season year


DATA_SOURCES: List[DataSource] = [
    DataSource(
        name="nfl_data_py",
        provider="nflfastR",
        description="Schedules, game metadata, play-by-play, team and player stats.",
        update_frequency=timedelta(days=1),
        retention_notes="Refresh after each game week; supports seasons 1999-present.",
        coverage_start=1999,
    ),
    DataSource(
        name="fivethirtyeight_elo",
        provider="FiveThirtyEight",
        description="Weekly team Elo ratings with QB adjustments and win probabilities.",
        update_frequency=timedelta(days=7),
        retention_notes="Pull latest CSV each Monday; archive historical snapshots.",
        coverage_start=2000,
    ),
    DataSource(
        name="the_odds_api",
        provider="The Odds API",
        description="Sportsbook moneyline, spread, and total odds snapshots.",
        update_frequency=timedelta(hours=6),
        retention_notes="Capture at multiple pre-game intervals and at close; track quota usage.",
    ),
    DataSource(
        name="mysportsfeeds",
        provider="MySportsFeeds",
        description="Player injuries, roster status, and depth chart changes.",
        update_frequency=timedelta(hours=12),
        retention_notes="Increase frequency Thu-Sun to capture late-breaking news.",
    ),
    DataSource(
        name="open_meteo",
        provider="Open-Meteo",
        description="Historical and forecasted weather for stadium locations.",
        update_frequency=timedelta(hours=24),
        retention_notes="Query archives for historical games; limit forecasts to outdoor venues.",
    ),
]
