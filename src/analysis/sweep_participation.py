"""
Sweep high-risk participation rate from 30% to 60%.
Find the crossover point where Smart Hotspot starts beating FCFS.
50 MC runs per rate, 6 workers parallel.
"""

import sys
sys.path.insert(0, "D:/Claude/BMP-Thesis/src")

import numpy as np
import time
from multiprocessing import Pool

HIGH_RISK_RATES = [0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
LOW_RATE = 0.55
MED_RATE = 0.45
INTERCEPT = -2.00
N_RUNS = 50


def run_one(args):
    seed, strategy_name, high_rate = args

    import model.environment as env_mod
    import model.adoption_function as adopt_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import FirstComeFirstServed, SmartHotspot
    from model.adoption_function import adoption_probability
    from model.simulation import FARM_TOTAL_CAP

    adopt_mod.PARAMS['intercept'] = INTERCEPT
    env = ThamesEnvironment(stochastic=True, seed=seed)

    participation_rates = {'Low': LOW_RATE, 'Medium': MED_RATE, 'High': high_rate}

    if strategy_name == 'FCFS':
        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
    else:
        strategy = SmartHotspot(subsidy_a=30, subsidy_b=30, seed=seed)

    env.reset()
    for farm in env.farms:
        farm._type_b_spent = 0
        farm.is_additional = False
    env.rng = np.random.RandomState(seed)

    rng2 = np.random.RandomState(seed + 50000)
    for farm in env.farms:
        rate = participation_rates.get(farm.risk_level, 0.40)
        farm._will_participate = rng2.random() < rate

    sim_rng = np.random.RandomState(seed)

    for year in range(1, 5):
        env.current_precip_multiplier = env.sample_precip_multiplier()
        total_cost = 0
        farm_order = strategy.order_farms(env.farms)

        for farm in farm_order:
            if not farm._will_participate:
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
                effective = actual_cost / max(farm.area_acres, 1)
                if effective < 5:
                    continue
                offer = {'type': offer['type'], 'subsidy_per_acre': effective,
                         'total_cost': actual_cost}
            prob = adoption_probability(farm, offer, rng=sim_rng)
            if sim_rng.random() < prob:
                farm.adopt(offer['type'], year)
                total_cost += actual_cost
                farm.total_subsidy_received += actual_cost
            if total_cost >= 4_350_000:
                break

    metrics = env.detailed_metrics(sample=False)
    return {
        'seed': seed,
        'strategy': strategy_name,
        'high_rate': high_rate,
        'y4_p': metrics['total_reduction_tonnes'],
        'y4_rate': sum(1 for f in env.farms if f.adopted) / len(env.farms),
    }


if __name__ == '__main__':
    print(f"High-risk participation sweep: {HIGH_RISK_RATES}")
    print(f"{N_RUNS} runs x {len(HIGH_RISK_RATES)} rates x 2 strategies = {N_RUNS * len(HIGH_RISK_RATES) * 2} jobs")

    jobs = []
    for rate in HIGH_RISK_RATES:
        for i in range(N_RUNS):
            jobs.append((i + 4000, 'FCFS', rate))
            jobs.append((i + 4000, 'Smart', rate))

    t0 = time.time()
    with Pool(processes=6) as pool:
        results = pool.map(run_one, jobs)
    print(f"Done in {time.time()-t0:.0f}s")

    print(f"\n{'='*70}")
    print(f"HIGH-RISK PARTICIPATION RATE SWEEP")
    print(f"{'='*70}")
    print(f"\n{'Rate':<8} {'FCFS P(t)':<12} {'Smart P(t)':<12} {'Diff(%)':<10} {'Win%':<8} {'Crossover?'}")
    print("-" * 65)

    crossover = None
    for rate in HIGH_RISK_RATES:
        fcfs_runs = [r for r in results if r['strategy'] == 'FCFS' and r['high_rate'] == rate]
        smart_runs = [r for r in results if r['strategy'] == 'Smart' and r['high_rate'] == rate]

        fcfs_p = np.mean([r['y4_p'] for r in fcfs_runs])
        smart_p = np.mean([r['y4_p'] for r in smart_runs])
        diff = (smart_p - fcfs_p) / fcfs_p * 100
        wins = np.mean([s['y4_p'] > f['y4_p'] for s, f in zip(smart_runs, fcfs_runs)])

        is_cross = ""
        if diff > 0 and crossover is None:
            crossover = rate
            is_cross = " ← CROSSOVER"

        print(f"  {rate:<6.0%} {fcfs_p:<12.1f} {smart_p:<12.1f} {diff:<+10.1f} {wins:<8.0%}{is_cross}")

    if crossover:
        print(f"\nCrossover at high-risk participation = {crossover:.0%}")
        print(f"Below {crossover:.0%}: FCFS wins (random coverage beats targeted non-participants)")
        print(f"Above {crossover:.0%}: Smart wins (enough high-risk farms participate to justify targeting)")
    else:
        print(f"\nNo crossover found — FCFS wins at all tested rates")
        print(f"Spatial targeting requires high-risk participation above 60%")
