# Thames River BMP Subsidy Allocation — Spatially-Explicit Simulation

Monte Carlo simulation of agricultural phosphorus Best Management Practice (BMP) subsidy allocation in the Upper Thames River watershed, Ontario. Evaluates five subsidy allocation strategies (FCFS baseline plus four alternative designs) against voluntary-participation constraints and phosphorus transport chain attribution across 8,949 agricultural fields.

**Manuscript**: [`paper/draft_FINAL.md`](paper/draft_FINAL.md)

## Summary of Findings

Under realistic participation constraints (55% low-risk / 45% medium-risk / 30% high-risk farmer willingness), the current first-come-first-served (FCFS) allocation achieves approximately **43 tonnes/year** total phosphorus reduction, or **~67% of the 64 t/yr target** for a 40% load reduction. All four alternative allocation designs perform equal to or worse than FCFS:

| Strategy | Total P (t/yr) | vs FCFS | Win rate |
|---|---|---|---|
| FCFS (baseline) | 42.8 [10.9, 119.2] | — | — |
| Naive Hotspot | 43.6 [11.3, 119.4] | +2.0% | 73% |
| Smart Hotspot | 42.2 [10.4, 118.6] | -1.6% | 31% |
| Efficiency Pricing ($15A/$60B) | 16.9 [4.4, 46.3] | -60.4% | 0% |
| Moderate Efficiency ($25A/$40B) | 20.4 [5.3, 54.6] | -52.2% | 0% |

Ranges are 95% empirical (2.5/97.5 percentile of 1,000-run Monte Carlo distribution). The structural gap between gross simulated reduction and the 40% target is driven by a risk-participation inversion: high-risk fields contributing 57% of phosphorus loading are operated by the farmers least likely to participate in voluntary programs. See manuscript for full analysis.

## Repository Structure

```
BMP-Thesis/
├── paper/                # Manuscript, figure captions, audit records
│   ├── draft_FINAL.md
│   ├── review_findings.md
│   └── CHANGELOG.md
├── src/
│   ├── model/            # Simulation core (agents, environment, strategies)
│   ├── data_prep/        # Spatial data processing (P-risk, fields, network)
│   └── analysis/         # Monte Carlo, sensitivity, figure scripts
├── data/
│   ├── raw/              # Downloaded public datasets
│   └── processed/        # Derived spatial layers
└── results/              # Monte Carlo outputs, figures, sensitivity results
```

## Reproducing the Results

Requirements: Python 3.11+ (tested on 3.13.2), ~14 CPU cores recommended, ~3 GB free disk.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download spatial data (runs ~5 min)
python src/data_prep/00_download_all_data.py

# 3. Build P-risk map and field-level agent layer (~10 min)
python src/data_prep/02_build_p_risk_map.py
python src/data_prep/03_build_field_agents.py

# 4. Run main Monte Carlo (1000 runs × 5 strategies, ~2.6 hr on 14 cores)
python src/analysis/monte_carlo.py

# 5. Run variance decomposition (~30 min)
python src/analysis/variance_decomposition.py

# 6. Run sensitivity analyses
python src/analysis/sensitivity_oat.py
python src/analysis/sweep_2d_participation.py

# 7. Generate figures from results
python src/analysis/generate_figures.py
```

Seeds are deterministic: main MC uses seeds 1000-1999; variance decomposition uses 8000-8999. Results should reproduce exactly to floating-point precision.

## Data Sources

All datasets are publicly available:
- **Soil survey**: Ontario Detailed Soil Survey (OMAFRA / OGDE)
- **Topography**: Ontario Hydro Network + SRTM DEM
- **Land use**: AAFC Annual Crop Inventory 2024
- **Watershed boundaries**: Ontario GeoHub (tertiary subwatersheds)
- **BMP program**: UTRCA Thames River Phosphorus Reduction Program public documentation

## Limitations

The simulation is a spatially-explicit stochastic model, not a calibrated hydrological transport model. Known limitations (see manuscript §7): voluntary participation rates are modeling assumptions; BMP effectiveness values are literature estimates with wide uncertainty; transport chain simplifications (static distance-to-water proxy, no in-stream routing); no climate variability; no farm-level exit or land tenure dynamics; one-at-a-time sensitivity does not capture parameter interactions.

## License

MIT License. See [`LICENSE`](LICENSE).

## Citation

If you use this code or data in your research, please cite the accompanying manuscript (citation to be added upon publication).
