"""
Monte Carlo: 1000 runs x 5 strategies — PARALLEL version.
Uses multiprocessing to maximize CPU utilization.
"""

import sys
sys.path.insert(0, "D:/Claude/BMP-Thesis/src")

import numpy as np
import json
import time
from pathlib import Path
from multiprocessing import Pool, cpu_count

N_RUNS = 1000
RESULTS_DIR = Path("D:/Claude/BMP-Thesis/results")
RESULTS_DIR.mkdir(exist_ok=True)


def run_batch(args):
    """Run one (seed, strategy_name) pair. Each worker loads its own env."""
    seed, strategy_name = args

    import model.adoption_function as adopt_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import (
        FirstComeFirstServed, HotspotPriority, SmartHotspot, EfficiencyPricing
    )
    from model.simulation import run_single_simulation

    adopt_mod.PARAMS['intercept'] = -2.00
    adopt_mod.PARAMS['subsidy_coeff'] = 0.010

    env = ThamesEnvironment(stochastic=True, seed=seed)

    if strategy_name == 'FCFS':
        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
    elif strategy_name == 'NaiveHotspot':
        strategy = HotspotPriority(high_subsidy=50, med_subsidy=30, seed=seed)
    elif strategy_name == 'SmartHotspot':
        strategy = SmartHotspot(subsidy_a=30, subsidy_b=30, seed=seed)
    elif strategy_name == 'EfficiencyPricing':
        strategy = EfficiencyPricing(subsidy_a=15, subsidy_b=60, seed=seed)
    elif strategy_name == 'ModerateEfficiency':
        strategy = EfficiencyPricing(subsidy_a=25, subsidy_b=40, seed=seed)

    run = run_single_simulation(env, strategy, years=4, seed=seed)
    y4 = run[-1]
    total_cost = sum(r['total_cost'] for r in run)

    return {
        'seed': seed,
        'strategy': strategy_name,
        'p_reduction_t': float(y4['p_reduction_tonnes']),
        'total_cost': float(total_cost),
        'adoption_rate': float(y4['adoption_rate']),
        'cost_per_kg': float(total_cost / max(y4['p_reduction_tonnes'] * 1000, 1)),
    }


if __name__ == '__main__':
    n_cores = cpu_count()
    n_workers = max(1, n_cores - 2)  # Leave 2 cores free

    print("=" * 60)
    print(f"MONTE CARLO: {N_RUNS} runs x 5 strategies — PARALLEL")
    print(f"CPU cores: {n_cores}, using {n_workers} workers")
    print("=" * 60)

    # Build all jobs
    strategies = ['FCFS', 'NaiveHotspot', 'SmartHotspot', 'EfficiencyPricing', 'ModerateEfficiency']
    jobs = []
    for i in range(N_RUNS):
        seed = i + 1000
        for s in strategies:
            jobs.append((seed, s))

    print(f"Total jobs: {len(jobs)}")

    t_start = time.time()
    with Pool(processes=n_workers) as pool:
        results = pool.map(run_batch, jobs)
    total_time = time.time() - t_start

    print(f"\nDone in {total_time:.0f}s ({total_time/60:.1f} min)")

    # Organize by strategy
    all_results = {s: [] for s in strategies}
    for r in results:
        all_results[r['strategy']].append(r)

    # Analysis
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    fcfs_p = np.array([r['p_reduction_t'] for r in all_results['FCFS']])

    summary = {}
    for name in strategies:
        p = np.array([r['p_reduction_t'] for r in all_results[name]])
        cost = np.array([r['cost_per_kg'] for r in all_results[name]])
        total = np.array([r['total_cost'] for r in all_results[name]])
        improvement = (p - fcfs_p) / fcfs_p * 100

        paired_diff = p - fcfs_p
        # Note: `_ci95` suffixes retained for JSON schema compatibility. These are
        # 2.5/97.5 percentile ranges of the MC distribution (95% empirical range),
        # not confidence intervals of the mean. See paper §4.5 for terminology.
        s = {
            'p_mean': float(np.mean(p)),
            'p_ci95': [float(np.percentile(p, 2.5)), float(np.percentile(p, 97.5))],
            'cost_per_kg_mean': float(np.mean(cost)),
            'total_cost_mean': float(np.mean(total)),
            'improvement_mean': float(np.mean(improvement)) if name != 'FCFS' else 0,
            'improvement_ci95': [float(np.percentile(improvement, 2.5)),
                                 float(np.percentile(improvement, 97.5))] if name != 'FCFS' else [0, 0],
            'paired_diff_mean': float(np.mean(paired_diff)) if name != 'FCFS' else 0,
            'paired_diff_ci95': [float(np.percentile(paired_diff, 2.5)),
                                 float(np.percentile(paired_diff, 97.5))] if name != 'FCFS' else [0, 0],
            'wins': int(np.sum(p > fcfs_p)) if name != 'FCFS' else N_RUNS,
        }
        summary[name] = s

        print(f"\n  {name}:")
        print(f"    P: {s['p_mean']:.1f}t [{s['p_ci95'][0]:.1f}, {s['p_ci95'][1]:.1f}]")
        print(f"    Cost: ${s['total_cost_mean']/1e6:.1f}M, ${s['cost_per_kg_mean']:.0f}/kg")
        if name != 'FCFS':
            print(f"    vs FCFS: {s['improvement_mean']:+.1f}% "
                  f"[{s['improvement_ci95'][0]:+.1f}%, {s['improvement_ci95'][1]:+.1f}%]")
            print(f"    Wins: {s['wins']}/{N_RUNS} ({s['wins']/N_RUNS*100:.1f}%)")

    # Save
    output = {
        'n_runs': N_RUNS,
        'total_time_s': total_time,
        'n_workers': n_workers,
        'summary': summary,
        'raw': {name: data for name, data in all_results.items()},
    }
    with open(RESULTS_DIR / "monte_carlo_results.json", 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nSaved to {RESULTS_DIR / 'monte_carlo_results.json'}")
