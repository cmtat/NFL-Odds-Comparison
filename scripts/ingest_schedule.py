"""Simple entrypoint to fetch NFL schedules using nfl_data_py."""

from __future__ import annotations

import argparse
from pathlib import Path

import nfl_data_py

from nfl_betting_model.config import paths


def ingest_schedule(season: int, output_dir: Path | None = None) -> Path:
    output_dir = output_dir or paths.data_raw / "schedule"
    output_dir.mkdir(parents=True, exist_ok=True)

    df = nfl_data_py.import_schedule([season])
    df["season"] = season

    output_path = output_dir / f"schedule_{season}.parquet"
    df.to_parquet(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest NFL schedule data.")
    parser.add_argument("season", type=int, help="Season year to ingest")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Optional override for the output directory (defaults to data/raw/schedule).",
    )
    args = parser.parse_args()

    path = ingest_schedule(args.season, args.output_dir)
    print(f"Wrote schedule data to {path}")


if __name__ == "__main__":
    main()
