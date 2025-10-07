# Data Inputs Blueprint

## 1. Scope
This document outlines the raw inputs required to train an NFL score-and-betting prediction model. Each section lists the fields to ingest, refresh cadence, integration keys, and downstream feature ideas.

## 2. Source Overview
| Source | Access | Data domains | Refresh cadence | Notes |
| --- | --- | --- | --- | --- |
| `nfl_data_py` | Python package (`nfl_data_py.importer`) | Schedule, game metadata, team & player stats (traditional + advanced), play-by-play | Weekly in-season, ad-hoc off-season | Mirrors official NFL Game Statistics via `nflfastR` |
| FiveThirtyEight Elo | Public CSV (`https://projects.fivethirtyeight.com/nfl-api/nfl_elo.csv`) | Team Elo & QB adjustments | Weekly | Provides pre/post-game Elo, win probabilities |
| The Odds API | REST (`https://api.the-odds-api.com/`) | Moneyline, spread, total prices across books | Daily; capture pre-open → close | Free tier 500 req/mo; monitor quota |
| MySportsFeeds | REST (`/v3/nfl`) | Injuries, roster status, depth charts | Daily, heavier Thu–Sun | Requires free dev account (rate limits) |
| Open-Meteo | REST (`https://api.open-meteo.com/`) | Historical & forecast weather | Daily or pre-game | No API key; query by stadium lat/long |
| Action Network (optional) | Web scrape | Public betting ticket/handle % | 2–3x weekly | Respect robots.txt & caching |

## 3. `nfl_data_py` Assets
### 3.1 Game schedule & metadata
- Endpoint: `import_schedule([seasons])`, `import_ngs_team_shot_data()` (if needed)
- Keep: `game_id`, `season`, `week`, `game_type`, `gameday`, `gamedate`, `gametime`, `home_team`, `away_team`, `home_coach`, `away_coach`, `stadium`, `surface`, `roof`, `temperature`, `wind`, `spread_line`, `total_line`, `div_game`, `home_result`, `away_result`.
- Use `game_id` as primary key; derive kickoff UTC, rest days, travel distance.

### 3.2 Team-level stats
- Endpoint: `import_team_stats([seasons])`.
- Metrics: offensive/defensive EPA per play, success rate, yards per play, drive stats, red-zone efficiency, turnover EPA, rush/pass rates, pressure rate, blitz rate, penalties.
- Aggregations: per-game, rolling 3/5-game averages, season-to-date percentiles.

### 3.3 Player-level stats
- Endpoint: `import_player_stats([seasons])`, `import_ngs_receiving()`, etc.
- Metrics: QB cpoe, EPA/dropback, air yards, rushing share, target share, YAC, pass rush win rate proxies.
- Derived features: team-level weighted player form, replacement-level indicators when starters injured.

### 3.4 Play-by-play detail
- Endpoint: `import_pbp_data([seasons])`.
- Fields: `play_id`, `posteam`, `defteam`, `yardline_100`, `down`, `ydstogo`, `passer_player_name`, `rusher_player_name`, `epa`, `success`, `wp`, `cp`, `qb_epa`, `air_yards`, `run_location`, penalties, drive identifiers.
- Derive situational splits (early vs late downs, red zone, under pressure) and explosive play rates.

## 4. FiveThirtyEight Elo
- Fetch CSV once per week (Monday AM).
- Keep columns: `season`, `week`, `team1`, `team2`, `elo1_pre`, `elo2_pre`, `elo1_post`, `elo2_post`, `qb1_value`, `qb2_value`, `qb1_adj`, `qb2_adj`, `qb1_health`, `qb2_health`, `neutral`, `playoff`, `elo_prob1`. Rename to align with team abbreviations from `nfl_data_py`.
- Derived: momentum metrics (`elo_post - elo_pre`), power differential, QB adjustment deltas.

## 5. The Odds API (sportsbooks)
- Endpoint: `/v4/sports/americanfootball_nfl/odds/` with params `regions=us`, `markets=h2h,spreads,totals`, `oddsFormat=american`.
- Store pulls at: (a) 72h before kickoff, (b) 24h, (c) 1h pre, (d) closing if available. Add manual run for key line moves.
- Fields: `game_id` (map via kickoff datetime + team IDs), `bookmaker`, `market` (`h2h`, `spreads`, `totals`), `last_update`, `price`, `point` (for spreads/totals).
- Derived: consensus line (median), closing line value, line movement slope, implied probabilities, hold percentage.

## 6. MySportsFeeds (injuries & roster)
- Endpoints: `/players/injuries.json`, `/players.json`, `/teamRoster.json`.
- Capture daily from Wed–Sun; more frequent near kickoff.
- Fields: `player_id`, `firstName`, `lastName`, `teamAbbreviation`, `position`, `injuryStatus`, `injuryStartDate`, `injuryNotes`, `practiceParticipation`, `practiceStatus`, `expectedReturn`.
- Derived: availability flags by position group, count of offensive line starters missing, aggregate EPA lost based on player value weighting.

## 7. Open-Meteo (weather)
- Endpoint: `/v1/forecast` with `latitude`, `longitude`, `hourly=temperature_2m,precipitation,windspeed_10m,windgusts_10m,relativehumidity_2m`.
- Strategy: query (a) historical actuals using archive API, (b) pre-game forecasts at 24h and 6h.
- Map stadium geolocation table (lat/long, roof type). Include roof status override for indoor stadiums.
- Derived: weather severity index, wind cross-component vs field orientation, precipitation flag.

## 8. Action Network (public betting) — optional
- Scrape matchup pages for `spread`, `moneyline`, `over/under` ticket and handle percentages.
- Standardize on timestamps (UTC). Store as percentages plus difference from sportsbook consensus.
- Use only where coverage exists; add null handling to pipeline.

## 9. Master Data & Keys
- `game_id`: canonical id from `nfl_data_py`; cross-reference to odds/injuries via `(season, week, home_team, away_team)` with tolerance for name variants.
- `team_abbr`: maintain mapping table (nfl, elo, odds, msf) stored in `data/reference/team_aliases.csv`.
- `player_id`: use MySportsFeeds IDs; map to `gsis_id` from `nfl_data_py` player tables for joinability.
- `stadium_id`: create static reference with name, team, lat/long, surface, roof, timezone.

## 10. Data Layer Structure
- Raw zone: store API responses (JSON/CSV) by `source/date/request_window` for audit.
- Staging zone: normalized parquet tables per source (partition by season/week).
- Feature store: engineered tables keyed by `game_id` (team-level) and `game_id, team` (side-level), containing rolling stats, injuries, weather, odds, Elo.
- Label table: final scores (`home_score`, `away_score`), ATS result, total result, closing line value.

## 11. Pipeline Orchestration Checklist
1. Load new schedule entries (nfl_data_py) → update master game table.
2. Refresh team/player stats and rolling features.
3. Pull Elo CSV → integrate into `team_features`.
4. Collect odds snapshots → compute consensus & CLV metrics.
5. Update injury and roster availability flags.
6. Fetch weather forecasts/actuals.
7. (Optional) Update public betting sentiment.
8. Run validation checks (missing data, time alignment, duplicate keys).
9. Materialize feature matrix and labels for modeling.

## 12. Outstanding Decisions
- Storage engine (Parquet on S3 vs local DuckDB vs Postgres).
- Orchestration tool (prefect, airflow, dagster, makefiles).
- Injury-to-performance weighting method (EPA, PFF grades, custom model).
- Handling bye weeks and neutral site games for travel/rest features.
- Strategy for supplementing player grades (e.g., PFF) if licensing added later.

