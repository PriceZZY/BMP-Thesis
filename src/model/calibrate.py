import pathlib
"""
Calibration script: find adoption function parameters that match UTRCA Year 1 data.

Targets (from UTRCA Thames River Phosphorus Reduction Program Year 1):
  - New projects: ~595
  - New acres: ~35,000
  - P reduction: ~5.7 tonnes
  - Budget spent: ~$4.35M

Method: grid search over intercept and subsidy_coeff.

Note: this calibration script uses subsidy_b=20 (lower bound of the $20-30/acre
subsurface P placement range) as the Type B anchor. The selected intercept=-2.00
was subsequently validated under subsidy_b=30 (production setting in monte_carlo.py)
via pilot_participation.py, reproducing the observed 86% Year 1 budget utilization.
The paper reports production values ($30/acre).
"""

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

import numpy as np
from model.environment import ThamesEnvironment
from model.subsidy_strategies import FirstComeFirstServed, HotspotPriority, SmartHotspot
from model.simulation import simulate_program
from model.adoption_function import PARAMS

_REPO = pathlib.Path(__file__).resolve().parents[2]

# Calibration targets
TARGET_NEW_PROJECTS = 595
TARGET_NEW_ACRES = 35000
TARGET_P_REDUCTION_T = 5.7

# Parameter ranges to search
INTERCEPT_RANGE = np.arange(-4.0, -1.0, 0.25)
SUBSIDY_COEFF_RANGE = np.arange(0.01, 0.06, 0.005)

print("=" * 60)
print("CALIBRATION: Grid Search")
print("=" * 60)

# Load environment once
print("\nLoading environment...")
env = ThamesEnvironment(stochastic=False, seed=42)

# Verify P load after AG_FRACTION fix
metrics = env.detailed_metrics()
print(f"Base P load: {metrics['base_load_tonnes']:.1f} tonnes")
print(f"Target: ~300 tonnes")

best_score = float('inf')
best_params = {}
results = []

print(f"\nSearching {len(INTERCEPT_RANGE)} x {len(SUBSIDY_COEFF_RANGE)} = "
      f"{len(INTERCEPT_RANGE) * len(SUBSIDY_COEFF_RANGE)} parameter combinations...")

for intercept in INTERCEPT_RANGE:
    for subsidy_coeff in SUBSIDY_COEFF_RANGE:
        # Override adoption params
        PARAMS['intercept'] = intercept
        PARAMS['subsidy_coeff'] = subsidy_coeff

        # Reset and run Year 1 only
        env.reset()
        fcfs = FirstComeFirstServed(subsidy_a=30, subsidy_b=20, seed=42)
        year1_results = simulate_program(env, fcfs, years=1, seed=42)
        r = year1_results[0]

        # Compute error (weighted sum of squared relative errors)
        err_projects = ((r['new_adoptions'] - TARGET_NEW_PROJECTS) / TARGET_NEW_PROJECTS) ** 2
        err_acres = ((r['new_adoption_acres'] - TARGET_NEW_ACRES) / TARGET_NEW_ACRES) ** 2
        err_p = ((r['p_reduction_tonnes'] - TARGET_P_REDUCTION_T) / TARGET_P_REDUCTION_T) ** 2

        # Weight P reduction and projects more than acres
        total_err = 2 * err_projects + 1 * err_acres + 2 * err_p

        results.append({
            'intercept': intercept,
            'subsidy_coeff': subsidy_coeff,
            'new_adoptions': r['new_adoptions'],
            'new_acres': r['new_adoption_acres'],
            'p_reduction_t': r['p_reduction_tonnes'],
            'cost': r['total_cost'],
            'error': total_err
        })

        if total_err < best_score:
            best_score = total_err
            best_params = {
                'intercept': intercept,
                'subsidy_coeff': subsidy_coeff,
            }
            best_result = r

# Sort by error
results.sort(key=lambda x: x['error'])

print("\n" + "=" * 60)
print("TOP 10 PARAMETER COMBINATIONS")
print("=" * 60)
print(f"{'Intercept':>10} {'SubCoeff':>10} {'Projects':>10} {'Acres':>10} "
      f"{'P_red(t)':>10} {'Cost($)':>12} {'Error':>10}")
print("-" * 75)

for r in results[:10]:
    print(f"{r['intercept']:>10.2f} {r['subsidy_coeff']:>10.3f} "
          f"{r['new_adoptions']:>10} {r['new_acres']:>10.0f} "
          f"{r['p_reduction_t']:>10.1f} {r['cost']:>12,.0f} "
          f"{r['error']:>10.3f}")

print(f"\n{'='*60}")
print(f"BEST PARAMETERS")
print(f"{'='*60}")
print(f"  Intercept:    {best_params['intercept']:.2f}")
print(f"  Subsidy coeff: {best_params['subsidy_coeff']:.3f}")
print(f"\n  Results:")
print(f"  New projects:  {best_result['new_adoptions']} (target: {TARGET_NEW_PROJECTS})")
print(f"  New acres:     {best_result['new_adoption_acres']:.0f} (target: {TARGET_NEW_ACRES})")
print(f"  P reduction:   {best_result['p_reduction_tonnes']:.1f} t (target: {TARGET_P_REDUCTION_T})")
print(f"  Cost:          ${best_result['total_cost']:,.0f}")

# Now run full 4-year simulation with best parameters
print(f"\n{'='*60}")
print(f"FULL 4-YEAR RUN WITH CALIBRATED PARAMETERS")
print(f"{'='*60}")

PARAMS['intercept'] = best_params['intercept']
PARAMS['subsidy_coeff'] = best_params['subsidy_coeff']

# FCFS
env.reset()
fcfs = FirstComeFirstServed(subsidy_a=30, subsidy_b=20, seed=42)
print("\nFCFS (current policy):")
fcfs_results = simulate_program(env, fcfs, years=4, seed=42, verbose=True)

# Hotspot Priority
# HotspotPriority already imported above
env.reset()
hotspot = HotspotPriority(high_subsidy=50, med_subsidy=30, seed=42)
print("\nHotspot Priority (proposed):")
hotspot_results = simulate_program(env, hotspot, years=4, seed=42, verbose=True)

# Final comparison
print(f"\n{'='*60}")
print(f"CALIBRATED COMPARISON")
print(f"{'='*60}")
fcfs_p = fcfs_results[-1]['p_reduction_tonnes']
hot_p = hotspot_results[-1]['p_reduction_tonnes']
improvement = (hot_p - fcfs_p) / max(fcfs_p, 0.1) * 100

print(f"  FCFS Year 4 P reduction:    {fcfs_p:.1f} tonnes")
print(f"  Hotspot Year 4 P reduction: {hot_p:.1f} tonnes")
print(f"  Improvement:                {improvement:+.1f}%")
print(f"\n  FCFS cost/kg:    ${sum(r['total_cost'] for r in fcfs_results) / max(fcfs_p*1000, 1):,.0f}")
print(f"  Hotspot cost/kg: ${sum(r['total_cost'] for r in hotspot_results) / max(hot_p*1000, 1):,.0f}")

# Save calibrated params
print(f"\nCalibrated parameters saved. Update adoption_function.py with:")
print(f"  'intercept': {best_params['intercept']}")
print(f"  'subsidy_coeff': {best_params['subsidy_coeff']}")
