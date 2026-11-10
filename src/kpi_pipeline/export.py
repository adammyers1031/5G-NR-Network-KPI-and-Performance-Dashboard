"""Write the Power BI-ready star schema to disk."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .kpis import add_derived_columns, cell_kpis, daily_kpis, hourly_kpis

DIM_COLUMNS = ["site_id", "cell_id", "pci", "band", "arfcn"]


def build_dim_cell(df: pd.DataFrame) -> pd.DataFrame:
    """Unique cell dimension table."""
    available = [col for col in DIM_COLUMNS if col in df.columns]
    dim = df[available].drop_duplicates()
    if "cell_id" in dim.columns:
        dim = dim.sort_values("cell_id")
    return dim.reset_index(drop=True)


def _write(frame: pd.DataFrame, out_dir: Path, name: str, formats: tuple[str, ...]) -> list[Path]:
    written: list[Path] = []
    for fmt in formats:
        fmt = fmt.lower().strip()
        if fmt not in {"csv", "parquet"}:
            raise ValueError(f"Unsupported output format: {fmt!r} (use csv or parquet)")
        if fmt == "csv":
            path = out_dir / f"{name}.csv"
            frame.to_csv(path, index=False)
        else:
            path = out_dir / f"{name}.parquet"
            frame.to_parquet(path, index=False)
        written.append(path)
    return written


def write_outputs(
    clean_df: pd.DataFrame,
    out_dir: str | Path,
    formats: tuple[str, ...] = ("csv",),
) -> dict[str, list[Path]]:
    """Export fact/dimension/aggregate tables and return the written paths."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    derived = add_derived_columns(clean_df)

    fact_columns = [
        "timestamp", "date", "hour", "day_of_week",
        "site_id", "cell_id", "ue_id",
        "rsrp_dbm", "rsrq_db", "sinr_db", "cqi", "mcs_dl", "mcs_ul",
        "dl_throughput_mbps", "ul_throughput_mbps", "total_throughput_mbps",
        "prb_util_dl_pct", "prb_util_ul_pct", "latency_ms",
        "coverage_class", "quality_class",
        "rrc_setup_attempts", "rrc_setup_successes",
        "handover_attempts", "handover_successes", "session_dropped",
    ]
    fact = derived[[col for col in fact_columns if col in derived.columns]]

    tables = {
        "fact_signal_samples": fact,
        "dim_cell": build_dim_cell(derived),
        "agg_cell_kpis": cell_kpis(derived),
        "agg_cell_hourly": hourly_kpis(derived),
        "agg_cell_daily": daily_kpis(derived),
    }

    return {
        name: _write(frame, out_path, name, formats)
        for name, frame in tables.items()
    }
