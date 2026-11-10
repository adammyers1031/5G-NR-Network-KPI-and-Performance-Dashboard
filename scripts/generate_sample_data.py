"""Generate realistic synthetic 5G NR measurement logs.

The output mimics a raw cell-tower log export: one row per UE measurement
sample, with signal metrics, throughput, load and event flags.

Usage:
    python scripts/generate_sample_data.py --rows 50000 --out data/raw/raw_cell_logs.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CELLS = [
    {"site_id": "SITE-001", "cell_id": "CELL-001-1", "pci": 101, "band": "n78", "arfcn": 653333},
    {"site_id": "SITE-001", "cell_id": "CELL-001-2", "pci": 102, "band": "n78", "arfcn": 653333},
    {"site_id": "SITE-001", "cell_id": "CELL-001-3", "pci": 103, "band": "n41", "arfcn": 518000},
    {"site_id": "SITE-002", "cell_id": "CELL-002-1", "pci": 201, "band": "n78", "arfcn": 653333},
    {"site_id": "SITE-002", "cell_id": "CELL-002-2", "pci": 202, "band": "n41", "arfcn": 518000},
    {"site_id": "SITE-002", "cell_id": "CELL-002-3", "pci": 203, "band": "n71", "arfcn": 123400},
    {"site_id": "SITE-003", "cell_id": "CELL-003-1", "pci": 301, "band": "n78", "arfcn": 653333},
    {"site_id": "SITE-003", "cell_id": "CELL-003-2", "pci": 302, "band": "n41", "arfcn": 518000},
    {"site_id": "SITE-003", "cell_id": "CELL-003-3", "pci": 303, "band": "n71", "arfcn": 123400},
    {"site_id": "SITE-004", "cell_id": "CELL-004-1", "pci": 401, "band": "n78", "arfcn": 653333},
    {"site_id": "SITE-004", "cell_id": "CELL-004-2", "pci": 402, "band": "n41", "arfcn": 518000},
    {"site_id": "SITE-004", "cell_id": "CELL-004-3", "pci": 403, "band": "n71", "arfcn": 123400},
]


def generate(rows: int = 50_000, seed: int = 42, days: int = 14) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    n_cells = len(CELLS)
    cell_index = rng.integers(0, n_cells, rows)

    # Per-cell radio quality offset (some cells are simply better placed).
    cell_offset = rng.normal(0.0, 4.0, n_cells)
    # Per-cell traffic weight (busier cells pull more PRB utilisation).
    cell_load = rng.uniform(0.7, 1.3, n_cells)

    start = pd.Timestamp("2026-10-01 00:00:00")
    offsets_min = rng.integers(0, days * 24 * 60, rows)
    timestamps = start + pd.to_timedelta(offsets_min, unit="m")

    hour = timestamps.hour.to_numpy()
    # Diurnal traffic curve: quiet at night, busy 08:00-20:00.
    diurnal = 0.55 + 0.45 * np.sin((hour - 6) / 24 * 2 * np.pi) ** 2

    # Radio measurements -----------------------------------------------------
    rsrp = -82.0 + cell_offset[cell_index] + rng.normal(0.0, 9.0, rows)
    rsrp = np.clip(rsrp, -132.0, -55.0)

    sinr = 12.0 + (rsrp + 95.0) * 0.25 + rng.normal(0.0, 5.0, rows)
    sinr = np.clip(sinr, -12.0, 32.0)

    rsrq = -8.0 + (rsrp + 95.0) * 0.06 + rng.normal(0.0, 2.0, rows)
    rsrq = np.clip(rsrq, -20.0, -3.0)

    cqi = np.clip(np.round((sinr + 5.0) / 2.2), 1, 15)
    mcs_dl = np.clip(np.round((cqi - 1) * 2 + rng.normal(0, 1, rows)), 0, 28)
    mcs_ul = np.clip(np.round((cqi - 1) * 1.4 + rng.normal(0, 1, rows)), 0, 28)

    # Load and throughput ----------------------------------------------------
    prb_dl = np.clip(
        rng.normal(55.0, 15.0, rows) * diurnal * cell_load[cell_index], 3.0, 99.0
    )
    prb_ul = np.clip(prb_dl * rng.uniform(0.15, 0.45, rows), 1.0, 95.0)

    load_penalty = 1.0 - 0.35 * (prb_dl / 100.0)
    dl_throughput = np.clip((sinr + 5.0) * 18.0 * load_penalty + rng.normal(0, 35, rows), 0, 1200)
    ul_throughput = np.clip((sinr + 5.0) * 4.0 * load_penalty + rng.normal(0, 10, rows), 0, 200)

    latency = np.clip(15.0 + 60.0 / (cqi + 1) + rng.normal(0, 4, rows), 3.0, 150.0)

    # Event flags ------------------------------------------------------------
    drop_prob = np.clip(0.002 + 0.06 * np.exp(-(sinr + 5.0) / 5.0), 0.0, 0.35)
    session_dropped = rng.random(rows) < drop_prob

    rrc_attempts = rng.random(rows) < 0.20
    rrc_success_prob = np.clip(0.999 - 0.02 * (sinr < -3), 0.0, 1.0)
    rrc_successes = rrc_attempts & (rng.random(rows) < rrc_success_prob)

    ho_attempts = rng.random(rows) < 0.06
    ho_success_prob = np.clip(0.995 - 0.03 * (sinr < 0), 0.0, 1.0)
    ho_successes = ho_attempts & (rng.random(rows) < ho_success_prob)

    frame = pd.DataFrame(
        {
            "timestamp": timestamps,
            "site_id": [CELLS[i]["site_id"] for i in cell_index],
            "cell_id": [CELLS[i]["cell_id"] for i in cell_index],
            "pci": [CELLS[i]["pci"] for i in cell_index],
            "band": [CELLS[i]["band"] for i in cell_index],
            "arfcn": [CELLS[i]["arfcn"] for i in cell_index],
            "ue_id": [f"UE-{value:07d}" for value in rng.integers(0, 20_000, rows)],
            "rsrp_dbm": np.round(rsrp, 2),
            "rsrq_db": np.round(rsrq, 2),
            "sinr_db": np.round(sinr, 2),
            "cqi": cqi.astype(int),
            "mcs_dl": mcs_dl.astype(int),
            "mcs_ul": mcs_ul.astype(int),
            "dl_throughput_mbps": np.round(dl_throughput, 2),
            "ul_throughput_mbps": np.round(ul_throughput, 2),
            "prb_util_dl_pct": np.round(prb_dl, 2),
            "prb_util_ul_pct": np.round(prb_ul, 2),
            "latency_ms": np.round(latency, 2),
            "rrc_setup_attempts": rrc_attempts.astype(int),
            "rrc_setup_successes": rrc_successes.astype(int),
            "handover_attempts": ho_attempts.astype(int),
            "handover_successes": ho_successes.astype(int),
            "session_dropped": session_dropped.astype(int),
        }
    )

    return frame.sort_values("timestamp").reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate synthetic 5G NR measurement logs.")
    parser.add_argument("--rows", type=int, default=50_000, help="Number of samples to generate")
    parser.add_argument("--days", type=int, default=14, help="Time span in days")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--out", default="data/raw/raw_cell_logs.csv", help="Output CSV path"
    )
    args = parser.parse_args()

    frame = generate(rows=args.rows, seed=args.seed, days=args.days)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_path, index=False)

    print(f"Wrote {len(frame):,} samples to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
