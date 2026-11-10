"""Convenience wrapper so the pipeline runs without ``pip install -e .``.

Usage:
    python scripts/run_pipeline.py --raw-dir data/raw --out-dir data/processed
"""

from __future__ import annotations

import sys
from pathlib import Path

# Make ``src`` importable when running straight from a clone.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from kpi_pipeline.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
