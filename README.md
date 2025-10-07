# NFL AI Final Score & Betting Edge Model

This repository is being repurposed into an end-to-end AI platform that predicts NFL final scores and surfaces betting edges. The long-term goal is to ingest multi-source football data, engineer features, train predictive models, and deliver automated betting recommendations for upcoming games.

## Project Objectives
- **Score prediction:** Forecast home/away final scores, point differential, and total points for every NFL matchup.
- **Bet selection:** Compare model outputs to market lines to highlight positive expected value (EV) opportunities across moneyline, spread, and totals markets.
- **Transparent pipeline:** Maintain reproducible data ingestion, feature engineering, model training, and evaluation workflows.

## Repository Layout
```
.
├── app.py                # Legacy Flask app placeholder (to be deprecated/refactored)
├── docs/                 # Planning and specification documents
│   └── data_requirements.md
├── data/
│   ├── raw/              # Unprocessed ingested data (API dumps, CSVs, etc.)
│   └── processed/        # Cleaned datasets and engineered features
├── examples/             # Sample inputs (legacy odds comparison examples)
├── models/               # Trained model artifacts and experiment metadata
├── notebooks/            # Exploratory analysis and prototyping notebooks
├── src/                  # Future Python package for data pipelines and modeling
├── static/, templates/   # Legacy web assets (to be evaluated for reuse)
└── requirements.txt      # Dependency specification (will be updated as scope evolves)
```

## Current Focus
1. **Data Requirements (complete):** `docs/data_requirements.md` outlines the datasets and providers needed for the score prediction model.
2. **Roadmap Definition (up next):** Draft technical roadmap covering ingestion pipelines, feature stores, and modeling experiments.
3. **Environment Bootstrap:** Align Python dependencies, linting, and testing frameworks with the new ML focus.

## Getting Started
- Review the data requirements document to understand data domains, cadence, and quality expectations.
- Evaluate access to prioritized sources (nflfastR, betting market APIs, injury feeds) and confirm licensing constraints.
- Begin drafting ERDs and data contracts for games, teams, players, and market odds.

## Contributing
1. Create feature branches off the `work` branch for scoped changes (e.g., `feature/data-model`, `feature/ingestion-scripts`).
2. Submit pull requests detailing scope, testing, and data implications.
3. Keep documentation up to date as we iterate on the data architecture and modeling approach.

## Legacy Code Notice
The previous odds comparison application remains in the repository for reference. Portions of the legacy codebase may be repurposed, but expect significant refactoring or removal as we progress toward the new AI modeling objectives.
