import pathlib
"""
Robustness check: invert participation rates.
High risk 55%, Low risk 30% (opposite of default).
If conclusion flips, it's not robust. If it holds, it's robust.
50 runs x 2 strategies, 6 workers.
"""
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import time
from multiprocessing import Pool

_REPO = pathlib.Path(__file__).resolve().parents[2]

# INVERTED rates
PARTICIPATION = {'Low': 0.30, 'Medium': 0.45, 'High': 0.55}
INTERCEPT = -2.00
N_RUNS = 50


def run_one(args):
    seed, strategy_name = args

    import model.adoption_function as adopt_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import FirstComeFirstServed, SmartHotspot
    from model.adoption_function import adoption_probability
    from model.simulation import FARM_TOTAL_CAP

    adopt_mod.PARAMS['intercept'] = INTERCEPT
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

    rng2 = np.random.RandomState(seed + 50000)
    for farm in env.farms:
        rate = PARTICIPATION.get(farm.risk_level, 0.40)
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
        'y4_p': metrics['total_reduction_tonnes'],
    }


if __name__ == '__main__':
    print(f"ROBUSTNESS CHECK: Inverted participation rates")
    print(f"  High risk: {PARTICIPATION['High']:.0%} (was 30%)")
    print(f"  Low risk:  {PARTICIPATION['Low']:.0%} (was 55%)")

    jobs = [(i + 6000, s) for i in range(N_RUNS) for s in ['FCFS', 'Smart']]

    t0 = time.time()
    with Pool(processes=6) as pool:
        results = pool.map(run_one, jobs)
    print(f"Done in {time.time()-t0:.0f}s")

    fcfs = [r for r in results if r['strategy'] == 'FCFS']
    smart = [r for r in results if r['strategy'] == 'Smart']

    fcfs_p = np.mean([r['y4_p'] for r in fcfs])
    smart_p = np.mean([r['y4_p'] for r in smart])
    diff = (smart_p - fcfs_p) / fcfs_p * 100
    wins = np.mean([s['y4_p'] > f['y4_p'] for s, f in zip(smart, fcfs)])

    print(f"\nResults (inverted participation):")
    print(f"  FCFS:  {fcfs_p:.1f}t")
    print(f"  Smart: {smart_p:.1f}t")
    print(f"  Diff:  {diff:+.1f}%")
    print(f"  Smart win rate: {wins:.0%}")

    if diff > 0:
        print(f"\n  CONCLUSION FLIPS: Smart wins when high-risk participation is high.")
        print(f"  This confirms: spatial targeting effectiveness depends on who participates.")
    else:
        print(f"\n  CONCLUSION HOLDS: FCFS still wins even with inverted rates.")
