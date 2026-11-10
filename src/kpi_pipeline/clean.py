"""Validation and cleaning for raw measurement samples."""

from __future__ import annotations

import pandas as pd

from .config import NUMERIC_BOUNDS

NUMERIC_COLUMNS = [
    "rsrp_dbm",
    "rsrq_db",
    "sinr_db",
    "cqi",
    "mcs_dl",
    "mcs_ul",
    "dl_throughput_mbps",
    "ul_throughput_mbps",
    "prb_util_dl_pct",
    "prb_util_ul_pct",
    "latency_ms",
    "rrc_setup_attempts",
    "rrc_setup_successes",
    "handover_attempts",
    "handover_successes",
    "session_dropped",
]

REQUIRED_COLUMNS = ["timestamp", "site_id", "cell_id", "rsrp_dbm", "sinr_db", "rsrq_db"]


def clean_samples(df: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned, de-duplicated copy of raw measurement samples.

    Steps:
    1. Parse timestamps and drop rows with no usable timestamp or cell identity.
    2. Coerce numeric KPI columns to numbers.
    3. Clip values to physically plausible bounds.
    4. Drop duplicate measurements for the same timestamp/cell/UE.
    5. Sort chronologically.
    """
    if df.empty:
        return df.copy()

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Raw logs are missing required columns: {missing}")

    out = df.copy()

    out["timestamp"] = pd.to_datetime(out["timestamp"], errors="coerce", utc=True)
    out = out.dropna(subset=["timestamp", "site_id", "cell_id"])
    # Drop the timezone so exported files stay simple for Power BI.
    out["timestamp"] = out["timestamp"].dt.tz_localize(None)

    for col in NUMERIC_COLUMNS:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out.dropna(subset=["rsrp_dbm", "sinr_db", "rsrq_db"])

    for col, (low, high) in NUMERIC_BOUNDS.items():
        if col in out.columns:
            out[col] = out[col].clip(lower=low, upper=high)

    dedupe_keys = [col for col in ("timestamp", "cell_id", "ue_id") if col in out.columns]
    if dedupe_keys:
        out = out.drop_duplicates(subset=dedupe_keys, keep="last")

    out = out.sort_values("timestamp").reset_index(drop=True)

    # Event flags must be 0/1 for the rate calculations.
    for col in ("rrc_setup_attempts", "rrc_setup_successes",
                "handover_attempts", "handover_successes", "session_dropped"):
        if col in out.columns:
            out[col] = (out[col].fillna(0) > 0).astype(int)

    return out
