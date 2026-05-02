"""
Pilot: EfficiencyPricing vs FCFS with participation filter.
50 runs, 6 workers.
"""
import sys
sys.path.insert(0, "D:/Claude/BMP-Thesis/src")

import numpy as np
import time
from multiprocessing import Pool

PARTICIPATION = {'Low': 0.55, 'Medium': 0.45, 'High': 0.30}
INTERCEPT = -2.00
N_RUNS = 50


def run_one(args):
    seed, strategy_name = args

    import model.adoption_function as adopt_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import FirstComeFirstServed, EfficiencyPricing
    from model.adoption_function import adoption_probability
    from model.simulation import FARM_TOTAL_CAP

    adopt_mod.PARAMS['intercept'] = INTERCEPT
    env = ThamesEnvironment(stochastic=True, seed=seed)

    if strategy_name == 'FCFS':
        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
    else:
        strategy = EfficiencyPricing(subsidy_a=15, subsidy_b=60, seed=seed)

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

    # Count Type B adoptions
    type_b = sum(1 for f in env.farms if f.has_type_b)
    type_a = sum(1 for f in env.farms if f.has_type_a)

    return {
        'seed': seed,
        'strategy': strategy_name,
        'y4_p': metrics['total_reduction_tonnes'],
        'y4_bioavail': metrics['bioavailable_reduction_tonnes'],
        'y4_pp_red': metrics['pp_reduction_tonnes'],
        'y4_drp_red': metrics['drp_reduction_tonnes'],
        'y4_rate': sum(1 for f in env.farms if f.adopted) / len(env.farms),
        'type_a_count': type_a,
        'type_b_count': type_b,
        'total_cost': 0,  # not tracked in this pilot
    }


if __name__ == '__main__':
    print(f"EfficiencyPricing vs FCFS pilot: {N_RUNS} runs")

    jobs = []
    for i in range(N_RUNS):
        jobs.append((i + 5000, 'FCFS'))
        jobs.append((i + 5000, 'Efficiency'))

    t0 = time.time()
    with Pool(processes=6) as pool:
        results = pool.map(run_one, jobs)
    print(f"Done in {time.time()-t0:.0f}s")

    fcfs = [r for r in results if r['strategy'] == 'FCFS']
    effi = [r for r in results if r['strategy'] == 'Efficiency']

    print(f"\n{'='*70}")
    print(f"EFFICIENCY PRICING vs FCFS (with participation filter)")
    print(f"{'='*70}")

    for name, data in [('FCFS ($30A/$30B)', fcfs), ('Efficiency ($15A/$60B)', effi)]:
        p = np.mean([r['y4_p'] for r in data])
        bio = np.mean([r['y4_bioavail'] for r in data])
        pp = np.mean([r['y4_pp_red'] for r in data])
        drp = np.mean([r['y4_drp_red'] for r in data])
        rate = np.mean([r['y4_rate'] for r in data])
        ta = np.mean([r['type_a_count'] for r in data])
        tb = np.mean([r['type_b_count'] for r in data])
        print(f"\n  {name}:")
        print(f"    Total P reduced: {p:.1f}t")
        print(f"    Bioavailable P:  {bio:.1f}t")
        print(f"    PP reduced:      {pp:.1f}t")
        print(f"    DRP reduced:     {drp:.1f}t")
        print(f"    Adoption rate:   {rate:.1%}")
        print(f"    Type A adopted:  {ta:.0f}")
        print(f"    Type B adopted:  {tb:.0f}")

    fcfs_p = np.mean([r['y4_p'] for r in fcfs])
    effi_p = np.mean([r['y4_p'] for r in effi])
    fcfs_bio = np.mean([r['y4_bioavail'] for r in fcfs])
    effi_bio = np.mean([r['y4_bioavail'] for r in effi])

    print(f"\n  Total P: Efficiency vs FCFS: {(effi_p-fcfs_p)/fcfs_p*100:+.1f}%")
    print(f"  BioP:    Efficiency vs FCFS: {(effi_bio-fcfs_bio)/fcfs_bio*100:+.1f}%")
