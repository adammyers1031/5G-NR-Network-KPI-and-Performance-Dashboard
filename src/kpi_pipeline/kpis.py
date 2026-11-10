"""Derived columns and KPI aggregations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import CQI_GOOD, RSRP_GOOD_DBM, RSRP_POOR_DBM, RSRQ_GOOD_DB, SINR_GOOD_DB

GROUP_KEYS = ["site_id", "cell_id"]


def _pct(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Percentage, returning NaN where the denominator is zero."""
    safe_denominator = denominator.replace(0, np.nan)
    return (numerator / safe_denominator) * 100.0


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Add time dimensions, coverage/quality flags and throughput totals."""
    out = df.copy()
    ts = pd.to_datetime(out["timestamp"])

    out["date"] = ts.dt.date
    out["hour"] = ts.dt.hour
    out["day_of_week"] = ts.dt.day_name()

    out["is_good_rsrp"] = out["rsrp_dbm"] >= RSRP_GOOD_DBM
    out["is_poor_rsrp"] = out["rsrp_dbm"] < RSRP_POOR_DBM
    out["is_good_sinr"] = out["sinr_db"] >= SINR_GOOD_DB
    out["is_good_rsrq"] = out["rsrq_db"] >= RSRQ_GOOD_DB
    out["is_good_cqi"] = out["cqi"] >= CQI_GOOD

    out["total_throughput_mbps"] = out["dl_throughput_mbps"] + out["ul_throughput_mbps"]

    out["coverage_class"] = pd.cut(
        out["rsrp_dbm"],
        bins=[-np.inf, RSRP_POOR_DBM, RSRP_GOOD_DBM, np.inf],
        labels=["Poor", "Fair", "Good"],
    )
    out["quality_class"] = pd.cut(
        out["sinr_db"],
        bins=[-np.inf, 0, SINR_GOOD_DB, 13, np.inf],
        labels=["Bad", "Weak", "Good", "Excellent"],
    )
    return out


def cell_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """One row per cell with the headline network KPIs."""
    agg = (
        df.groupby(GROUP_KEYS, dropna=False)
        .agg(
            samples=("rsrp_dbm", "size"),
            avg_rsrp_dbm=("rsrp_dbm", "mean"),
            p10_rsrp_dbm=("rsrp_dbm", lambda s: s.quantile(0.10)),
            avg_rsrq_db=("rsrq_db", "mean"),
            avg_sinr_db=("sinr_db", "mean"),
            avg_cqi=("cqi", "mean"),
            avg_mcs_dl=("mcs_dl", "mean"),
            avg_prb_util_dl_pct=("prb_util_dl_pct", "mean"),
            avg_dl_throughput_mbps=("dl_throughput_mbps", "mean"),
            avg_ul_throughput_mbps=("ul_throughput_mbps", "mean"),
            avg_latency_ms=("latency_ms", "mean"),
            rrc_attempts=("rrc_setup_attempts", "sum"),
            rrc_successes=("rrc_setup_successes", "sum"),
            ho_attempts=("handover_attempts", "sum"),
            ho_successes=("handover_successes", "sum"),
            drops=("session_dropped", "sum"),
            good_rsrp_pct=("is_good_rsrp", "mean"),
            poor_rsrp_pct=("is_poor_rsrp", "mean"),
            good_sinr_pct=("is_good_sinr", "mean"),
        )
        .reset_index()
    )

    agg["accessibility_pct"] = _pct(agg["rrc_successes"], agg["rrc_attempts"])
    agg["handover_success_pct"] = _pct(agg["ho_successes"], agg["ho_attempts"])
    agg["drop_rate_pct"] = _pct(agg["drops"], agg["samples"])
    agg["good_rsrp_pct"] *= 100.0
    agg["poor_rsrp_pct"] *= 100.0
    agg["good_sinr_pct"] *= 100.0

    # Simple 0-100 health score; every component is already a percentage.
    agg["compliance_score"] = agg[
        ["accessibility_pct", "handover_success_pct", "good_rsrp_pct", "good_sinr_pct"]
    ].mean(axis=1)

    return agg.sort_values("cell_id").reset_index(drop=True)


def hourly_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """One row per cell per hour, for time-series visuals in Power BI."""
    keys = ["date", "hour", *GROUP_KEYS]
    agg = (
        df.groupby(keys, dropna=False)
        .agg(
            samples=("rsrp_dbm", "size"),
            avg_rsrp_dbm=("rsrp_dbm", "mean"),
            avg_sinr_db=("sinr_db", "mean"),
            avg_cqi=("cqi", "mean"),
            avg_prb_util_dl_pct=("prb_util_dl_pct", "mean"),
            avg_dl_throughput_mbps=("dl_throughput_mbps", "mean"),
            avg_ul_throughput_mbps=("ul_throughput_mbps", "mean"),
            drops=("session_dropped", "sum"),
        )
        .reset_index()
    )
    agg["drop_rate_pct"] = _pct(agg["drops"], agg["samples"])
    return agg.sort_values(keys).reset_index(drop=True)


def daily_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """One row per cell per day, useful for trend lines."""
    keys = ["date", *GROUP_KEYS]
    agg = (
        df.groupby(keys, dropna=False)
        .agg(
            samples=("rsrp_dbm", "size"),
            avg_rsrp_dbm=("rsrp_dbm", "mean"),
            avg_sinr_db=("sinr_db", "mean"),
            avg_dl_throughput_mbps=("dl_throughput_mbps", "mean"),
            avg_ul_throughput_mbps=("ul_throughput_mbps", "mean"),
            drops=("session_dropped", "sum"),
            good_rsrp_pct=("is_good_rsrp", "mean"),
        )
        .reset_index()
    )
    agg["drop_rate_pct"] = _pct(agg["drops"], agg["samples"])
    agg["good_rsrp_pct"] *= 100.0
    return agg.sort_values(keys).reset_index(drop=True)
