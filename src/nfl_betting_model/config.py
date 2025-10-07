"""Project-wide configuration helpers."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    """Canonical filesystem locations used throughout the project."""

    root: Path = Path(__file__).resolve().parents[2]
    data_raw: Path = root / "data" / "raw"
    data_staging: Path = root / "data" / "staging"
    data_features: Path = root / "data" / "features"
    docs: Path = root / "docs"
    notebooks: Path = root / "notebooks"
    scripts: Path = root / "scripts"


paths = ProjectPaths()
