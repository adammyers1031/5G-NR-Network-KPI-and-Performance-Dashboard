"""End-to-end smoke test for the export layer."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from generate_sample_data import generate  # noqa: E402

from kpi_pipeline.clean import clean_samples  # noqa: E402
from kpi_pipeline.export import write_outputs  # noqa: E402


def test_end_to_end_export(tmp_path: Path) -> None:
    raw = generate(rows=2_000, seed=7, days=2)
    cleaned = clean_samples(raw)

    outputs = write_outputs(cleaned, tmp_path, formats=("csv",))

    expected = {
        "fact_signal_samples",
        "dim_cell",
        "agg_cell_kpis",
        "agg_cell_hourly",
        "agg_cell_daily",
    }
    assert set(outputs) == expected

    kpis = pd.read_csv(tmp_path / "agg_cell_kpis.csv")
    assert len(kpis) == 12  # twelve synthetic cells
    assert kpis["avg_rsrp_dbm"].between(-140, -40).all()
    assert kpis["accessibility_pct"].between(0, 100).all()

    fact = pd.read_csv(tmp_path / "fact_signal_samples.csv")
    assert len(fact) == len(cleaned)
    assert {"coverage_class", "quality_class", "total_throughput_mbps"}.issubset(fact.columns)
