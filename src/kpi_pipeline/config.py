"""Project paths and operator-tunable KPI thresholds."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"
POWERBI_DIR = PROJECT_ROOT / "powerbi"

# 3GPP-inspired KPI thresholds. Tune these to the operator's planning targets.
RSRP_GOOD_DBM = -95.0  # >= this value counts as "good" coverage
RSRP_POOR_DBM = -105.0  # < this value counts as "poor" coverage
RSRQ_GOOD_DB = -12.0
SINR_GOOD_DB = 5.0
CQI_GOOD = 10

# Physical / operational bounds used to reject obviously corrupt readings.
NUMERIC_BOUNDS: dict[str, tuple[float, float]] = {
    "rsrp_dbm": (-140.0, -40.0),
    "rsrq_db": (-20.0, -3.0),
    "sinr_db": (-20.0, 40.0),
    "cqi": (0.0, 15.0),
    "mcs_dl": (0.0, 28.0),
    "mcs_ul": (0.0, 28.0),
    "dl_throughput_mbps": (0.0, 2000.0),
    "ul_throughput_mbps": (0.0, 500.0),
    "prb_util_dl_pct": (0.0, 100.0),
    "prb_util_ul_pct": (0.0, 100.0),
    "latency_ms": (0.0, 500.0),
}
