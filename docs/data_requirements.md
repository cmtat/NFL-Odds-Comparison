# Data Requirements for NFL Score Prediction Model

To transform this repository into an AI system that forecasts final scores and betting edges for NFL games, we need a rich, well-governed dataset. The following sections outline the core data domains, key features, potential sources, refresh cadence, and quality considerations required for the first modeling milestone.

## 1. Game Context and Scheduling
- **Season structure:** week number, regular season vs. playoffs, game date/time, rest days since each team’s previous game, travel distance/time zones.
- **Venue metadata:** stadium, surface type, indoor/outdoor, historical scoring environment, weather controls (if roof can open/close).
- **Broadcast info (optional):** primetime flag, short-week indicator (e.g., Thursday Night Football).
- **Sources:** NFL Game Statistics & Information System (GSIS), Sports Reference, nflfastR schedule datasets.
- **Cadence:** publish full schedule pre-season; update weekly for flexed games and kickoff adjustments.

## 2. Team Performance History
- **Final scores & outcomes:** team points for/against, scoring by quarter, overtime indicators.
- **Efficiency metrics:** offensive/defensive EPA per play, success rate, drive-level stats, explosive play rates, third/fourth-down conversions, red-zone efficiency.
- **Play type splits:** rush/pass attempts, play-action usage, RPO rates, screen usage.
- **Tempo metrics:** seconds per play, no-huddle frequency, pace when leading/trailing.
- **Sources:** nflfastR play-by-play data, TruMedia (if accessible), PFF for advanced stats.
- **Cadence:** update after every completed game.

## 3. Player Availability and Performance
- **Injury reports:** practice participation, game status (questionable/doubtful/out), injured reserve activations/returns.
- **Roster depth charts:** starters, positional replacements, offensive line continuity, secondary coverage matchups.
- **Player-level metrics:** QB efficiency (EPA/CPOE composite), RB receiving/rushing splits, WR/TE target share and air yards, defender pressure rates, coverage grades.
- **Transactions:** trades, signings, suspensions.
- **Sources:** NFL weekly injury reports, team depth chart releases, Pro Football Focus, FantasyPros (for aggregated practice statuses).
- **Cadence:** daily during game weeks; final inactives 90 minutes pre-kickoff.

## 4. Betting Market Signals
- **Pre-game odds:** moneyline, spread, total from sharp books (Pinnacle, Circa, Bookmaker).
- **Line movement history:** opening odds, key adjustments, closing line.
- **Derivative markets:** team totals, alternate spreads/totals to anchor implied distributions.
- **Consensus probabilities:** vig-free implied probabilities, market-derived expected score (from spread/total).
- **Sources:** The Odds API, Unabated, PFF Bets, Sports Insights.
- **Cadence:** intraday snapshots every 15-30 minutes; final closing line capture.

## 5. Environmental Factors
- **Weather forecasts:** temperature, wind speed/direction, precipitation probability, humidity, field conditions.
- **Historical weather impact:** team performance vs. weather regimes (e.g., wind > 15 mph).
- **Sources:** NOAA API, OpenWeatherMap, stadium-specific weather services.
- **Cadence:** hourly updates from 72 hours pre-kickoff until game start.

## 6. Opponent Tendencies and Matchups
- **Scheme indicators:** offensive/defensive formations, personnel group usage, blitz rates, coverage shells, motion usage.
- **Matchup deltas:** OL vs. DL pressure win rates, WR vs. CB coverage mismatches, run gap success.
- **Sources:** Next Gen Stats, PFF charting, SIS DataHub.
- **Cadence:** weekly updates tied to coaching adjustments and opponent scouting.

## 7. Label Construction for Modeling
- **Target variables:** home/away final score, point differential, total points, cover flags (spread, total, moneyline).
- **Derived targets:** implied team totals (from spread/total), win probability deltas vs. market.
- **Temporal alignment:** ensure all features are frozen as-of pre-game cutoff to avoid leakage.

## 8. Data Governance & Storage
- **Schema design:** normalized relational schema (PostgreSQL) or feature store with partitioning by season/week.
- **Versioning:** maintain raw ingests, processed features, and feature store snapshots for reproducibility.
- **Quality checks:** completeness, freshness, outlier detection, injury status conflicts.
- **Access control:** store API credentials securely (e.g., environment variables, secret manager).

## Next Steps
1. **Source evaluation:** finalize which providers grant permissible access for commercial or research use.
2. **Data model draft:** design entity-relationship diagrams for teams, games, players, bets.
3. **Ingestion roadmap:** prioritize schedule/box score, betting markets, injuries for minimum viable dataset.
4. **Feature spec:** translate above metrics into engineered features grouped by availability window (early-week vs. gameday).

This document will evolve as we validate data availability, provider costs, and model performance requirements.
