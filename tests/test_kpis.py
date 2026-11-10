from __future__ import annotations

import pandas as pd
import pytest

from kpi_pipeline.kpis import add_derived_columns, cell_kpis, hourly_kpis


@pytest.fixture()
def sample_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-01-01 00:00", periods=4, freq="h"),
            "site_id": ["S1"] * 4,
            "cell_id": ["C1"] * 4,
            "rsrp_dbm": [-80.0, -100.0, -110.0, -90.0],
            "rsrq_db": [-8.0, -12.0, -16.0, -9.0],
            "sinr_db": [20.0, 5.0, -5.0, 12.0],
            "cqi": [14, 9, 3, 11],
            "mcs_dl": [25, 15, 4, 20],
            "mcs_ul": [18, 10, 3, 14],
            "prb_util_dl_pct": [50.0, 60.0, 80.0, 40.0],
            "prb_util_ul_pct": [10.0, 15.0, 25.0, 8.0],
            "dl_throughput_mbps": [400.0, 200.0, 50.0, 350.0],
            "ul_throughput_mbps": [80.0, 40.0, 10.0, 70.0],
            "latency_ms": [10.0, 20.0, 50.0, 12.0],
            "rrc_setup_attempts": [1, 1, 1, 0],
            "rrc_setup_successes": [1, 1, 0, 0],
            "handover_attempts": [0, 1, 1, 0],
            "handover_successes": [0, 1, 0, 0],
            "session_dropped": [0, 0, 1, 0],
        }
    )


def test_add_derived_columns(sample_frame: pd.DataFrame) -> None:
    out = add_derived_columns(sample_frame)

    assert out["is_good_rsrp"].tolist() == [True, False, False, True]
    assert out["is_poor_rsrp"].tolist() == [False, False, True, False]
    assert out["is_good_sinr"].tolist() == [True, True, False, True]
    assert out["total_throughput_mbps"].tolist() == [480.0, 240.0, 60.0, 420.0]
    assert out["coverage_class"].astype(str).tolist() == ["Good", "Fair", "Poor", "Good"]


def test_cell_kpi_rates(sample_frame: pd.DataFrame) -> None:
    derived = add_derived_columns(sample_frame)
    kpis = cell_kpis(derived)
    row = kpis.iloc[0]

    assert row["samples"] == 4
    assert row["accessibility_pct"] == pytest.approx(66.6667, rel=1e-3)
    assert row["handover_success_pct"] == pytest.approx(50.0)
    assert row["drop_rate_pct"] == pytest.approx(25.0)
    assert row["good_rsrp_pct"] == pytest.approx(50.0)
    assert row["good_sinr_pct"] == pytest.approx(75.0)
    assert row["avg_dl_throughput_mbps"] == pytest.approx(250.0)


def test_cell_kpi_handles_zero_denominators(sample_frame: pd.DataFrame) -> None:
    frame = sample_frame.copy()
    frame["handover_attempts"] = 0
    frame["handover_successes"] = 0

    kpis = cell_kpis(add_derived_columns(frame))

    assert pd.isna(kpis.iloc[0]["handover_success_pct"])


def test_hourly_kpis_shape(sample_frame: pd.DataFrame) -> None:
    hourly = hourly_kpis(add_derived_columns(sample_frame))

    assert len(hourly) == 4  # four distinct hours
    assert {"date", "hour", "avg_rsrp_dbm", "drop_rate_pct"}.issubset(hourly.columns)
