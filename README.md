# NFL Betting Model

This repository houses an end-to-end workflow for forecasting NFL game scores and identifying betting edges across major markets (spread, moneyline, and totals).

## Project Overview
- **Data ingestion**: Collect schedules, stats, odds, injuries, weather, and sentiment from the free sources documented in `docs/data_inputs.md`.
- **Feature engineering**: Build team and player rolling metrics, adjust for availability, market movement, and environmental context.
- **Modeling**: Train machine learning models to predict final scores and recommend bets with measured edge (TBD).

## Getting Started
1. Install Python 3.10+.
2. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```
3. Run the sample ingestion script to download schedule data:
   ```bash
   python scripts/ingest_schedule.py 2023
   ```

## Repository Layout
- `src/nfl_betting_model/`: Core Python package for configuration, schemas, and (future) pipelines.
- `scripts/`: Command-line utilities for data ingestion.
- `data/`: Storage for raw, staging, and feature-layer datasets.
- `tests/`: Test suite.
- `docs/`: Documentation, including the data input blueprint.
- `notebooks/`: Exploratory analysis and prototyping space.

## Next Steps
- Implement ingestion modules for each data source described in `docs/data_inputs.md`.
- Define feature engineering pipelines and model training workflows.
- Set up continuous integration to lint and test incoming changes.
