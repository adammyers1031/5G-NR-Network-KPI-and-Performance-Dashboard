# Power BI Dashboard

This folder documents the Power BI report that sits on top of the Python output.
The `.pbix` file itself is **not** committed (binary, hard to review); the data
model, DAX measures and visual spec live here so the report can be rebuilt.

## 1. Run the pipeline

From the repo root:

```powershell
python scripts/generate_sample_data.py --rows 50000
python scripts/run_pipeline.py --format csv,parquet
```

Tables land in `data/processed/`:

| Table | Grain | Role |
|---|---|---|
| `fact_signal_samples` | one UE measurement sample | fact |
| `dim_cell` | one row per cell | dimension |
| `agg_cell_kpis` | one row per cell | pre-aggregated summary |
| `agg_cell_hourly` | one row per cell per hour | time series |
| `agg_cell_daily` | one row per cell per day | trend lines |

## 2. Load the data

1. Open Power BI Desktop → **Get data → Text/CSV** (or **Parquet**).
2. Load `fact_signal_samples`, `dim_cell`, `agg_cell_daily`, `agg_cell_hourly`.
3. In **Model view**, create the relationships:
   - `dim_cell[cell_id]` (1) → `fact_signal_samples[cell_id]` (*)
   - `dim_cell[cell_id]` (1) → `agg_cell_daily[cell_id]` (*)
4. Create the `Date` calculated table from `kpi_measures.dax`, then
   **Table tools → Mark as date table**, and relate `Date[Date]` to
   `fact_signal_samples[date]`.

## 3. Add the measures

Copy the blocks from [`kpi_measures.dax`](./kpi_measures.dax) into
**Modeling → New measure**.

## 4. Recommended report pages

**Page 1 — Network overview**
- KPI cards: Compliance Score, Good Coverage %, Accessibility %, Drop Rate %
- Map or bar chart: Average RSRP by site
- Line chart: Average DL throughput by hour of day
- Matrix: cells × KPI Status

**Page 2 — Cell performance**
- Scatter: Avg SINR (x) vs Avg DL Throughput (y), size = sample count
- Bar chart: cells ranked by Compliance Score
- Slicers: band, site, date range

**Page 3 — Coverage & quality**
- Histogram of RSRP (`coverage_class` buckets)
- Stacked column: coverage class share per site
- Heatmap: hour × cell, value = average SINR

## 5. Refresh

Point the CSV/Parquet connectors at the stable output paths in
`data/processed/`. Re-running the pipeline overwrites the files, so a
**Refresh** in Power BI picks up the new data without re-modelling.

> Tip: schedule the Python pipeline with Windows Task Scheduler or GitHub
> Actions, then use the Power BI gateway to refresh on a schedule.
