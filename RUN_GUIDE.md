# Reviewer Run Guide

This guide lets a reviewer **verify the headline results in under 15 minutes** without re-running the full 2.6-hour Monte Carlo. A full reproduction path is provided at the end.

---

## 0. What ships in this repository

| Path | Size | Contents |
|---|---|---|
| `src/` | — | All Python source (model, data prep, analysis) |
| `data/processed/` | 27 MB | Derived spatial layers (P-risk map, field agents, watershed boundary) |
| `results/` | 13 MB | Pre-computed Monte Carlo outputs and rendered figures |
| `paper/draft_FINAL.md` | — | Manuscript |
| `requirements.txt` | — | Pinned Python dependencies |

`data/raw/` (1.7 GB of public Ontario soil / land-use / DEM downloads) is **not** committed; rebuild it from sources via `src/data_prep/00_download_all_data.py` if you want to re-derive `data/processed/` from scratch (Step 4 below).

---

## 1. Environment setup (5 minutes)

Requirements: **Python 3.11+** (tested on 3.13.2), ~3 GB free disk for the no-raw-data path. Tested on Windows 11 with 14 CPU cores.

```bash
git clone https://github.com/PriceZZY/BMP-Thesis.git
cd BMP-Thesis
pip install -r requirements.txt
```

If `pip install` fails on `geopandas` / `rasterio` (common on Windows due to GDAL binaries), use conda instead:

```bash
conda install -c conda-forge geopandas rasterio fiona shapely pyproj
pip install -r requirements.txt   # remaining packages
```

---

## 2. Reproduce all 9 figures from stored Monte Carlo results (5 minutes)

The repository ships with `results/monte_carlo_results.json` containing the 1,000-run Monte Carlo distribution for all five strategies. To regenerate every figure from these results without re-running the simulation:

```bash
python src/analysis/generate_figures.py
```

Output: 9 PNG/PDF figures written to `results/figures/`, matching Figures 1–9 in the manuscript.

---

## 3. Spot-check the headline numbers (1 minute)

Open `results/monte_carlo_results.json` and confirm the per-strategy means match Table 3 of the manuscript:

| Strategy | Mean total P (t/yr) | vs FCFS |
|---|---|---|
| FCFS (baseline) | 42.8 | — |
| Naive Hotspot | 43.6 | +2.0% |
| Smart Hotspot | 42.2 | −1.6% |
| Efficiency Pricing ($15A/$60B) | 16.9 | −60.4% |
| Moderate Efficiency ($25A/$40B) | 20.4 | −52.2% |

Other stored result files for cross-reference:
- `results/variance_decomposition.json` — precipitation share of variance (manuscript §5.4)
- `results/sweep_2d_results.json` — 2D participation rate sweep (manuscript Fig. 9 / §5.6)
- `results/sensitivity_oat_results.json` — one-at-a-time sensitivity (manuscript Fig. 8)

---

## 4. Full reproduction from scratch (~3 hours)

```bash
# Download all public spatial data (~5 min, fetches ~1.7 GB into data/raw/)
python src/data_prep/00_download_all_data.py

# Rebuild P-risk map and 8,949-field agent layer (~10 min)
python src/data_prep/02_build_p_risk_map.py
python src/data_prep/03_build_field_agents.py

# Main Monte Carlo: 1,000 runs × 5 strategies (~2.6 hr on 14 cores)
python src/analysis/monte_carlo.py

# Variance decomposition (~30 min)
python src/analysis/variance_decomposition.py

# Sensitivity analyses (~20 min total)
python src/analysis/sensitivity_oat.py
python src/analysis/sweep_2d_participation.py

# Regenerate all figures
python src/analysis/generate_figures.py
```

**Determinism**: main MC uses seeds 1000–1999; variance decomposition uses seeds 8000–8999. Re-running with the same seeds reproduces the manuscript values to floating-point precision.

---

## 5. Hardware notes

- The simulation uses `multiprocessing` to parallelise across Monte Carlo runs.
- 14 cores were used for the manuscript timings. Fewer cores work but scale roughly linearly.
- Memory footprint: ~2 GB peak (8,949 field agents × 1,000 runs).

---

## 6. Where each manuscript result lives in the code

| Manuscript section | Code file |
|---|---|
| §2 Phosphorus transport framework (Fig. 1) | `src/analysis/figure1_transport_chain.py` |
| §3 P-risk classification (Fig. 2) | `src/data_prep/02_build_p_risk_map.py`, `src/analysis/fig2_prisk_map.py` |
| §4 Simulation core | `src/model/simulation.py`, `src/model/farm_agent.py`, `src/model/environment.py` |
| §4 Adoption function | `src/model/adoption_function.py` |
| §4.5 Calibration | `src/model/calibrate.py` |
| §5 Strategy comparison (Fig. 3, Table 3) | `src/analysis/monte_carlo.py` |
| §5.4 Variance decomposition (precip share) | `src/analysis/variance_decomposition.py` |
| §5.5 Robustness with inverted assumption | `src/analysis/robustness_inverted.py` |
| §5.6 2D participation sweep (Fig. 9) | `src/analysis/sweep_2d_participation.py` |
| §5.7 OAT sensitivity (Fig. 8) | `src/analysis/sensitivity_oat.py` |
| Pilot participation filter (§5.2) | `src/model/pilot_participation.py` |
| Subsidy allocation strategies (§4.3) | `src/model/subsidy_strategies.py` |

---

## 7. Issues / contact

For questions or reproduction problems, open an issue on the GitHub repository or contact the author at z427zhou@uwaterloo.ca.
