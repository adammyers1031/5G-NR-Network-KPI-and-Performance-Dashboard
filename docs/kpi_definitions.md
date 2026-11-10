# KPI Definitions

Thresholds are defined in [`src/kpi_pipeline/config.py`](../src/kpi_pipeline/config.py)
and can be tuned per operator. Defaults are inspired by common 3GPP / operator
planning targets.

## Signal quality

| KPI | Unit | Definition | "Good" threshold |
|---|---|---|---|
| RSRP | dBm | Reference Signal Received Power, per sample | ≥ −95 dBm |
| RSRQ | dB | Reference Signal Received Quality | ≥ −12 dB |
| SINR | dB | Signal-to-Interference-plus-Noise Ratio | ≥ 5 dB |
| CQI | index (0–15) | Channel Quality Indicator | ≥ 10 |
| MCS | index (0–28) | Modulation and Coding Scheme | — |

Coverage classes derived from RSRP:

- **Good**: ≥ −95 dBm
- **Fair**: −105 dBm to −95 dBm
- **Poor**: < −105 dBm

SINR quality classes: **Bad** (< 0 dB), **Weak** (0–5 dB), **Good** (5–13 dB),
**Excellent** (≥ 13 dB).

## Throughput & load

| KPI | Unit | Definition |
|---|---|---|
| DL throughput | Mbps | Mean downlink throughput per sample |
| UL throughput | Mbps | Mean uplink throughput per sample |
| PRB utilisation DL/UL | % | Mean physical resource block utilisation |
| Latency | ms | Mean user-plane latency |

## Mobility & retainability

| KPI | Formula |
|---|---|
| Accessibility % | Σ RRC setup successes ÷ Σ RRC setup attempts × 100 |
| Handover success % | Σ handover successes ÷ Σ handover attempts × 100 |
| Drop rate % | Σ dropped sessions ÷ total samples × 100 |

All rate KPIs return `null` (NaN) when the denominator is zero, rather than a
misleading 0 %.

## Composite score

```
Compliance Score = mean(Accessibility %, Handover Success %, Good Coverage %, Good SINR %)
```

Status bands: **Healthy** ≥ 90, **Watch** 75–90, **Critical** < 75.

## Data quality rules

The cleaning stage (`src/kpi_pipeline/clean.py`) enforces:

1. A parseable timestamp and non-null `site_id` / `cell_id`.
2. Numeric coercion of every KPI column.
3. Physical bounds (e.g. RSRP between −140 and −40 dBm, CQI 0–15).
4. De-duplication on `(timestamp, cell_id, ue_id)`.
5. Boolean event flags normalised to 0/1.
