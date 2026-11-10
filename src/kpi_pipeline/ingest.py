"""Load raw cell-tower logs from disk."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_raw_logs(raw_dir: str | Path, pattern: str = "*.csv") -> pd.DataFrame:
    """Concatenate every CSV matching ``pattern`` under ``raw_dir``.

    A ``source_file`` column is added so rows stay traceable back to the file
    they came from. Returns an empty frame when nothing matches.
    """
    raw_path = Path(raw_dir)
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw data directory does not exist: {raw_path}")

    files = sorted(raw_path.glob(pattern))
    frames: list[pd.DataFrame] = []
    for file in files:
        frame = pd.read_csv(file)
        frame["source_file"] = file.name
        frames.append(frame)

    if not frames:
        return pd.DataFrame()

    return pd.concat(frames, ignore_index=True, sort=False)
