"""
2D Participation Rate Sweep: high-risk vs low-risk participation rates.
Each combo: 100 MC runs x 2 strategies (FCFS vs Smart).
Output: heat map of Smart vs FCFS improvement.
Uses shared environment loaded once, passed to workers via global.
"""
import sys
sys.path.insert(0, "D:/Claude/BMP-Thesis/src")

import numpy as np
import json
import time
from multiprocessing import Pool
from pathlib import Path

RESULTS = Path("D:/Claude/BMP-Thesis/results")
FIGURES = RESULTS / "figures"

HIGH_RATES = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
LOW_RATES = [0.20, 0.30, 0.40, 0.50, 0.60, 0.70]
N_RUNS = 100


def run_combo(args):
    """Run one (high_rate, low_rate, seed, strategy) combination."""
    high_rate, low_rate, seed, strategy_name = args
    med_rate = (high_rate + low_rate) / 2

    import model.adoption_function as adopt_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import FirstComeFirstServed, SmartHotspot
    from model.adoption_function import adoption_probability
    from model.simulation import FARM_TOTAL_CAP

    adopt_mod.PARAMS['intercept'] = -2.00
    env = ThamesEnvironment(stochastic=True, seed=seed)

    if strategy_name == 'FCFS':
        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
    else:
        strategy = SmartHotspot(subsidy_a=30, subsidy_b=30, seed=seed)

    env.reset()
    for farm in env.farms:
        farm._type_b_spent = 0
        farm.is_additional = False
    env.rng = np.random.RandomState(seed)

    part_rng = np.random.RandomState(seed + 50000)
    rates = {'Low': low_rate, 'Medium': med_rate, 'High': high_rate}
    for farm in env.farms:
        farm._will_participate = part_rng.random() < rates.get(farm.risk_level, 0.40)

    sim_rng = np.random.RandomState(seed)
    for year in range(1, 5):
        env.current_precip_multiplier = env.sample_precip_multiplier()
        total_cost = 0
        for farm in strategy.order_farms(env.farms):
            if not getattr(farm, '_will_participate', True):
                continue
            remaining_cap = FARM_TOTAL_CAP - farm.total_subsidy_received
            if remaining_cap <= 0:
                continue
            remaining_budget = 4_350_000 - total_cost
            offer = strategy.allocate(farm, remaining_budget)
            if offer['type'] == 'none':
                continue
            actual_cost = min(offer['total_cost'], remaining_cap, remaining_budget)
            if actual_cost < offer['total_cost']:
                eff = actual_cost / max(farm.area_acres, 1)
                if eff < 5:
                    continue
                offer = {'type': offer['type'], 'subsidy_per_acre': eff, 'total_cost': actual_cost}
            prob = adoption_probability(farm, offer, rng=sim_rng)
            if sim_rng.random() < prob:
                farm.adopt(offer['type'], year)
                total_cost += actual_cost
                farm.total_subsidy_received += actual_cost
            if total_cost >= 4_350_000:
                break

    metrics = env.detailed_metrics(sample=False)
    return {
        'high_rate': high_rate, 'low_rate': low_rate,
        'seed': seed, 'strategy': strategy_name,
        'y4_p': metrics['total_reduction_tonnes'],
    }


if __name__ == '__main__':
    total_combos = len(HIGH_RATES) * len(LOW_RATES)
    total_jobs = total_combos * N_RUNS * 2
    print(f"2D Participation Sweep: {total_combos} combos x {N_RUNS} runs x 2 strategies = {total_jobs} jobs")

    jobs = []
    for hr in HIGH_RATES:
        for lr in LOW_RATES:
            for i in range(N_RUNS):
                seed = i + 7000
                jobs.append((hr, lr, seed, 'FCFS'))
                jobs.append((hr, lr, seed, 'Smart'))

    t0 = time.time()
    with Pool(processes=14) as pool:
        results = pool.map(run_combo, jobs)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.0f}s ({elapsed/60:.1f} min)")

    # Build heat map data
    heatmap = {}
    for hr in HIGH_RATES:
        for lr in LOW_RATES:
            fcfs_p = [r['y4_p'] for r in results
                      if r['high_rate'] == hr and r['low_rate'] == lr and r['strategy'] == 'FCFS']
            smart_p = [r['y4_p'] for r in results
                       if r['high_rate'] == hr and r['low_rate'] == lr and r['strategy'] == 'Smart']
            fcfs_mean = np.mean(fcfs_p)
            smart_mean = np.mean(smart_p)
            imp = (smart_mean - fcfs_mean) / fcfs_mean * 100 if fcfs_mean > 0 else 0
            wins = np.mean([s > f for s, f in zip(smart_p, fcfs_p)])
            heatmap[f"{hr:.2f}_{lr:.2f}"] = {
                'high_rate': hr, 'low_rate': lr,
                'fcfs_mean': float(fcfs_mean), 'smart_mean': float(smart_mean),
                'improvement': float(imp), 'win_rate': float(wins),
            }

    # Print grid
    print(f"\nSmart vs FCFS improvement (%):")
    print(f"{'':>8}", end='')
    for lr in LOW_RATES:
        print(f"  Low={lr:.0%}", end='')
    print()
    for hr in HIGH_RATES:
        print(f"Hi={hr:.0%}", end='')
        for lr in LOW_RATES:
            key = f"{hr:.2f}_{lr:.2f}"
            imp = heatmap[key]['improvement']
            print(f"  {imp:>+6.1f}%", end='')
        print()

    # Find crossover
    print("\nCrossover boundary (Smart > FCFS):")
    for hr in HIGH_RATES:
        for lr in LOW_RATES:
            key = f"{hr:.2f}_{lr:.2f}"
            if heatmap[key]['improvement'] > 0:
                print(f"  High={hr:.0%}, Low={lr:.0%}: Smart wins by {heatmap[key]['improvement']:+.1f}%")

    # Save
    with open(RESULTS / "sweep_2d_results.json", 'w') as f:
        json.dump(heatmap, f, indent=2)

    # Generate heat map figure
    import matplotlib.pyplot as plt

    grid = np.zeros((len(HIGH_RATES), len(LOW_RATES)))
    for i, hr in enumerate(HIGH_RATES):
        for j, lr in enumerate(LOW_RATES):
            grid[i, j] = heatmap[f"{hr:.2f}_{lr:.2f}"]['improvement']

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(grid, cmap='RdYlGn', aspect='auto', origin='lower',
                   vmin=-5, vmax=5)

    ax.set_xticks(range(len(LOW_RATES)))
    ax.set_xticklabels([f"{r:.0%}" for r in LOW_RATES])
    ax.set_yticks(range(len(HIGH_RATES)))
    ax.set_yticklabels([f"{r:.0%}" for r in HIGH_RATES])
    ax.set_xlabel('Low-Risk Participation Rate', fontsize=12)
    ax.set_ylabel('High-Risk Participation Rate', fontsize=12)
    ax.set_title('Smart Hotspot vs FCFS: Improvement by Participation Rates\n'
                 '(green = Smart wins, red = FCFS wins; Medium-risk = midpoint of High and Low)',
                 fontsize=13, fontweight='bold')

    # Add text annotations
    for i in range(len(HIGH_RATES)):
        for j in range(len(LOW_RATES)):
            val = grid[i, j]
            color = 'white' if abs(val) > 3 else 'black'
            ax.text(j, i, f"{val:+.1f}%", ha='center', va='center',
                    fontsize=10, fontweight='bold', color=color)

    # Add crossover line
    ax.contour(grid, levels=[0], colors='black', linewidths=2, linestyles='--')

    plt.colorbar(im, label='Smart Hotspot improvement over FCFS (%)')
    plt.tight_layout()
    plt.savefig(FIGURES / 'fig9_participation_heatmap.png', dpi=300, bbox_inches='tight')
    print(f"\nSaved fig9_participation_heatmap.png")
