import pathlib
"""
OAT Sensitivity Analysis — Multiprocessing version.
Parallelizes across parameter-value pairs using 8 processes.
"""

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import json
import time
from pathlib import Path
from multiprocessing import Pool, cpu_count

_REPO = pathlib.Path(__file__).resolve().parents[2]

RESULTS = (_REPO / "results")
N_RUNS = 100

SENSITIVITY_PARAMS = {
    'pp_drp_ratio': {
        'default': 0.80,
        'range': [0.70, 0.75, 0.80, 0.85, 0.90],
        'label': 'PP:DRP Ratio (PP fraction)',
    },
    'pp_bioavail': {
        'default': 0.25,
        'range': [0.15, 0.20, 0.25, 0.30, 0.35],
        'label': 'PP Bioavailability',
    },
    'tile_penalty': {
        'default': 0.50,
        'range': [0.20, 0.35, 0.50, 0.65, 0.80],
        'label': 'Tile Drain Type A Penalty',
    },
    'addit_low': {
        'default': 0.40,
        'range': [0.20, 0.30, 0.40, 0.50, 0.60],
        'label': 'Additionality Baseline (Low Risk)',
    },
    'addit_high': {
        'default': 0.10,
        'range': [0.05, 0.10, 0.15, 0.20, 0.30],
        'label': 'Additionality Baseline (High Risk)',
    },
    'bmp_a_high': {
        'default': 0.60,
        'range': [0.30, 0.45, 0.60, 0.75, 0.90],
        'label': 'Type A Effectiveness (High Risk)',
    },
    'bmp_b_high': {
        'default': 0.70,
        'range': [0.50, 0.60, 0.70, 0.80, 0.88],
        'label': 'Type B Effectiveness (High Risk)',
    },
    'base_p_high': {
        'default': 1.50,
        'range': [0.80, 1.10, 1.50, 1.75, 2.00],
        'label': 'Base P Loss (High Risk, kg/acre/yr)',
    },
    'peer_effect': {
        'default': 1.5,
        'range': [0.5, 1.0, 1.5, 2.0, 2.5],
        'label': 'Peer Effect Coefficient',
    },
}


def run_one_param_value(args):
    """Run N_RUNS MC iterations for one (param_name, value) pair.
    Each worker loads its own environment to avoid shared state.
    """
    param_name, value, n_runs = args

    # Import inside worker to get fresh module state
    import model.environment as env_mod
    import model.adoption_function as adopt_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import FirstComeFirstServed, SmartHotspot
    from model.simulation import run_single_simulation

    # Reset all defaults first
    env_mod.PARTICULATE_RATIO['mean'] = 0.80
    env_mod.PARTICULATE_RATIO['min'] = 0.70
    env_mod.PARTICULATE_RATIO['max'] = 0.90
    env_mod.TILE_DRAIN_TYPE_A_PENALTY = 0.50
    env_mod.BASELINE_ADOPTION['Low'] = 0.40
    env_mod.BASELINE_ADOPTION['Medium'] = 0.20
    env_mod.BASELINE_ADOPTION['High'] = 0.10
    env_mod.REDUCTION_A['High']['mean'] = 0.60
    env_mod.REDUCTION_B['High']['mean'] = 0.70
    env_mod.BASE_P_LOSS['High']['mean'] = 1.50
    adopt_mod.PARAMS['peer_coeff'] = 1.5

    # Set the one parameter being tested
    if param_name == 'pp_drp_ratio':
        env_mod.PARTICULATE_RATIO['mean'] = value
        env_mod.PARTICULATE_RATIO['min'] = max(0.5, value - 0.10)
        env_mod.PARTICULATE_RATIO['max'] = min(0.95, value + 0.10)
    elif param_name == 'tile_penalty':
        env_mod.TILE_DRAIN_TYPE_A_PENALTY = value
    elif param_name == 'addit_low':
        env_mod.BASELINE_ADOPTION['Low'] = value
    elif param_name == 'addit_high':
        env_mod.BASELINE_ADOPTION['High'] = value
    elif param_name == 'bmp_a_high':
        env_mod.REDUCTION_A['High']['mean'] = value
    elif param_name == 'bmp_b_high':
        env_mod.REDUCTION_B['High']['mean'] = value
    elif param_name == 'base_p_high':
        env_mod.BASE_P_LOSS['High']['mean'] = value
    elif param_name == 'peer_effect':
        adopt_mod.PARAMS['peer_coeff'] = value

    # Load environment (each worker gets its own)
    env = ThamesEnvironment(stochastic=True, seed=42)

    fcfs_p = []
    smart_p = []

    for i in range(n_runs):
        seed = i + 2000

        fcfs = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
        run_f = run_single_simulation(env, fcfs, years=4, seed=seed)
        fcfs_p.append(run_f[-1]['p_reduction_tonnes'])

        smart = SmartHotspot(subsidy_a=30, subsidy_b=30, seed=seed)
        run_s = run_single_simulation(env, smart, years=4, seed=seed)
        smart_p.append(run_s[-1]['p_reduction_tonnes'])

    fcfs_mean = float(np.mean(fcfs_p))
    smart_mean = float(np.mean(smart_p))
    improvement = (smart_mean - fcfs_mean) / fcfs_mean * 100 if fcfs_mean > 0 else 0
    target_pct = smart_mean / 64.0 * 100

    return {
        'param_name': param_name,
        'value': value,
        'fcfs_mean': fcfs_mean,
        'smart_mean': smart_mean,
        'improvement_pct': float(improvement),
        'target_achievement_pct': float(target_pct),
        'win_rate': float(np.mean([s > f for s, f in zip(smart_p, fcfs_p)])),
    }


if __name__ == '__main__':
    print("=" * 60)
    print(f"OAT SENSITIVITY ANALYSIS — PARALLEL ({N_RUNS} runs/value)")
    print(f"CPU cores: {cpu_count()}")
    print("=" * 60)

    # Build all (param, value) pairs
    all_jobs = []
    for pname, pinfo in SENSITIVITY_PARAMS.items():
        for val in pinfo['range']:
            all_jobs.append((pname, val, N_RUNS))

    print(f"\nTotal jobs: {len(all_jobs)} (9 params x 5 values)")
    print(f"Using 6 parallel workers (leaving 2 cores free)")

    t_start = time.time()

    with Pool(processes=6) as pool:
        results_list = pool.map(run_one_param_value, all_jobs)

    total_time = time.time() - t_start
    print(f"\nDone in {total_time:.0f}s ({total_time/60:.1f} min)")

    # Organize results by parameter
    all_results = {}
    for r in results_list:
        pname = r['param_name']
        if pname not in all_results:
            all_results[pname] = {
                'label': SENSITIVITY_PARAMS[pname]['label'],
                'default': SENSITIVITY_PARAMS[pname]['default'],
                'results': [],
            }
        all_results[pname]['results'].append({
            'value': r['value'],
            'fcfs_mean': r['fcfs_mean'],
            'smart_mean': r['smart_mean'],
            'improvement_pct': r['improvement_pct'],
            'target_achievement_pct': r['target_achievement_pct'],
            'win_rate': r['win_rate'],
        })

    # Sort each param's results by value
    for pname in all_results:
        all_results[pname]['results'].sort(key=lambda x: x['value'])

    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS BY PARAMETER")
    print("=" * 60)

    for pname, data in all_results.items():
        print(f"\n  {data['label']}:")
        for r in data['results']:
            is_def = " *" if abs(r['value'] - data['default']) < 0.001 else ""
            print(f"    {r['value']:.2f}{is_def}: FCFS={r['fcfs_mean']:.1f}t, "
                  f"Smart={r['smart_mean']:.1f}t, imp={r['improvement_pct']:+.1f}%, "
                  f"target={r['target_achievement_pct']:.0f}%")

    # Ranking
    print("\n" + "=" * 60)
    print("PARAMETER INFLUENCE RANKING")
    print("=" * 60)

    influences = []
    for name, data in all_results.items():
        imps = [r['improvement_pct'] for r in data['results']]
        tgts = [r['target_achievement_pct'] for r in data['results']]
        imp_range = max(imps) - min(imps)
        tgt_range = max(tgts) - min(tgts)
        influence = imp_range + tgt_range * 0.1
        influences.append((name, data['label'], imp_range, tgt_range, influence))

    influences.sort(key=lambda x: -x[4])

    print(f"\n  {'Parameter':<40} {'Imp% range':<12} {'Target% range':<14} {'Rating'}")
    print("  " + "-" * 75)
    for name, label, imp_r, tgt_r, infl in influences:
        stars = '***' if infl > 5 else '**' if infl > 2 else '*'
        print(f"  {label:<40} {imp_r:>6.1f}pp     {tgt_r:>8.0f}pp       {stars}")

    # Save
    output_path = RESULTS / "sensitivity_oat_results.json"
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved to {output_path}")
