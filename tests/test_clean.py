from __future__ import annotations

import pandas as pd
import pytest

from kpi_pipeline.clean import clean_samples


def test_clean_rejects_bad_timestamps_and_deduplicates() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": ["2026-01-01 00:00:00", "not-a-date", "2026-01-01 00:00:00"],
            "site_id": ["S1", "S1", "S1"],
            "cell_id": ["C1", "C1", "C1"],
            "ue_id": ["UE-1", "UE-1", "UE-1"],
            "rsrp_dbm": [-90.0, -90.0, -91.0],
            "sinr_db": [10.0, 10.0, 11.0],
            "rsrq_db": [-9.0, -9.0, -10.0],
        }
    )

    cleaned = clean_samples(frame)

    assert len(cleaned) == 1  # invalid timestamp dropped, duplicate collapsed
    assert cleaned.iloc[0]["rsrp_dbm"] == -91.0


def test_clean_clips_out_of_range_values() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": ["2026-01-01", "2026-01-02"],
            "site_id": ["S1", "S1"],
            "cell_id": ["C1", "C1"],
            "ue_id": ["UE-1", "UE-2"],
            "rsrp_dbm": [-200.0, 20.0],
            "sinr_db": [100.0, -100.0],
            "rsrq_db": [-40.0, 5.0],
        }
    )

    cleaned = clean_samples(frame)

    assert cleaned["rsrp_dbm"].tolist() == [-140.0, -40.0]
    assert cleaned["sinr_db"].tolist() == [40.0, -20.0]
    assert cleaned["rsrq_db"].tolist() == [-20.0, -3.0]


def test_clean_requires_columns() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        clean_samples(pd.DataFrame({"timestamp": ["2026-01-01"]}))
