import pathlib
"""
Pilot test: add participation filter before adoption decision.
Not all farmers are reachable — some never engage with government programs.

Participation rates (calibrated to UTRCA Year 1 budget utilization 86%; see paper §5.2):
  Low risk:  55% willing to participate
  Medium:    45% willing to participate
  High risk: 30% willing to participate

This filter is applied BEFORE the adoption probability calculation.
If a farmer won't participate, no subsidy amount will change their mind.

50 MC runs x 2 strategies to check Year 1 calibration.
"""

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

import numpy as np
import time
from multiprocessing import Pool

_REPO = pathlib.Path(__file__).resolve().parents[2]

# Participation rates
PARTICIPATION_RATES = {
    'Low': 0.55,
    'Medium': 0.45,
    'High': 0.30,
}

def run_one(args):
    seed, strategy_name = args

    import model.environment as env_mod
    import model.adoption_function as adopt_mod
    from model.environment import ThamesEnvironment
    from model.subsidy_strategies import FirstComeFirstServed, SmartHotspot
    from model.adoption_function import adoption_probability
    from model.simulation import (
        FARM_TOTAL_CAP, TYPE_B_CAP, COMBO_BONUS_PER_ACRE
    )

    # Adjust intercept: with participation filter pre-screening,
    # farms that enter adoption function are already "willing to consider",
    # so base adoption probability should be higher
    adopt_mod.PARAMS['intercept'] = -2.00

    env = ThamesEnvironment(stochastic=True, seed=seed)
    rng = np.random.RandomState(seed)

    # Assign participation willingness to each farm (fixed per farm per run)
    for farm in env.farms:
        rate = PARTICIPATION_RATES.get(farm.risk_level, 0.15)
        farm._will_participate = rng.random() < rate

    if strategy_name == 'FCFS':
        strategy = FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=seed)
    else:
        strategy = SmartHotspot(subsidy_a=30, subsidy_b=30, seed=seed)

    # Reset
    env.reset()
    for farm in env.farms:
        farm._type_b_spent = 0
        farm.is_additional = False
    env.rng = np.random.RandomState(seed)

    # Re-assign participation after reset
    rng2 = np.random.RandomState(seed + 50000)
    for farm in env.farms:
        rate = PARTICIPATION_RATES.get(farm.risk_level, 0.15)
        farm._will_participate = rng2.random() < rate

    # Run 4 years with participation filter
    yearly_results = []
    sim_rng = np.random.RandomState(seed)

    for year in range(1, 5):
        env.current_precip_multiplier = env.sample_precip_multiplier()
        total_cost = 0
        new_adoptions = 0
        new_acres = 0
        filtered_out = 0

        farm_order = strategy.order_farms(env.farms)

        for farm in farm_order:
            # PARTICIPATION FILTER — new addition
            if not farm._will_participate:
                filtered_out += 1
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
                new_adoptions += 1
                new_acres += farm.area_acres

            if total_cost >= 4_350_000:
                break

        metrics = env.detailed_metrics(sample=False)
        yearly_results.append({
            'year': year,
            'new_adoptions': new_adoptions,
            'new_acres': new_acres,
            'filtered_out': filtered_out,
            'adoption_rate': sum(1 for f in env.farms if f.adopted) / len(env.farms),
            'p_reduction_t': metrics['total_reduction_tonnes'],
            'total_cost': total_cost,
            'budget_util': total_cost / 4_350_000,
        })

    y4 = yearly_results[-1]
    return {
        'seed': seed,
        'strategy': strategy_name,
        'y1_adoptions': yearly_results[0]['new_adoptions'],
        'y1_acres': yearly_results[0]['new_acres'],
        'y1_p': yearly_results[0]['p_reduction_t'],
        'y1_cost': yearly_results[0]['total_cost'],
        'y1_budget_util': yearly_results[0]['budget_util'],
        'y1_filtered': yearly_results[0]['filtered_out'],
        'y4_p': y4['p_reduction_t'],
        'y4_rate': y4['adoption_rate'],
        'total_cost': sum(r['total_cost'] for r in yearly_results),
    }


if __name__ == '__main__':
    N = 50
    print(f"Participation filter pilot: {N} runs x 2 strategies")
    print(f"Rates: Low={PARTICIPATION_RATES['Low']:.0%}, "
          f"Med={PARTICIPATION_RATES['Medium']:.0%}, "
          f"High={PARTICIPATION_RATES['High']:.0%}")

    jobs = []
    for i in range(N):
        jobs.append((i + 3000, 'FCFS'))
        jobs.append((i + 3000, 'Smart'))

    t0 = time.time()
    with Pool(processes=6) as pool:
        results = pool.map(run_one, jobs)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.0f}s")

    fcfs = [r for r in results if r['strategy'] == 'FCFS']
    smart = [r for r in results if r['strategy'] == 'Smart']

    print(f"\n{'='*60}")
    print(f"YEAR 1 RESULTS (with participation filter)")
    print(f"{'='*60}")

    for name, data in [('FCFS', fcfs), ('Smart', smart)]:
        y1_adopt = np.mean([r['y1_adoptions'] for r in data])
        y1_acres = np.mean([r['y1_acres'] for r in data])
        y1_p = np.mean([r['y1_p'] for r in data])
        y1_cost = np.mean([r['y1_cost'] for r in data])
        y1_util = np.mean([r['y1_budget_util'] for r in data])
        y1_filt = np.mean([r['y1_filtered'] for r in data])
        print(f"\n  {name}:")
        print(f"    Y1 adoptions: {y1_adopt:.0f} (target: ~1200-1500 field-level)")
        print(f"    Y1 acres:     {y1_acres:.0f} (target: ~35,000)")
        print(f"    Y1 P reduced: {y1_p:.1f}t (target: ~5.7t)")
        print(f"    Y1 cost:      ${y1_cost:,.0f}")
        print(f"    Y1 budget:    {y1_util:.0%}")
        print(f"    Filtered out: {y1_filt:.0f} farms (non-participants)")

    print(f"\n{'='*60}")
    print(f"YEAR 4 RESULTS")
    print(f"{'='*60}")

    for name, data in [('FCFS', fcfs), ('Smart', smart)]:
        y4_p = np.mean([r['y4_p'] for r in data])
        y4_rate = np.mean([r['y4_rate'] for r in data])
        total = np.mean([r['total_cost'] for r in data])
        print(f"\n  {name}:")
        print(f"    Y4 P reduced: {y4_p:.1f}t")
        print(f"    Y4 adopt rate: {y4_rate:.1%}")
        print(f"    4yr total cost: ${total/1e6:.1f}M")

    fcfs_p4 = np.mean([r['y4_p'] for r in fcfs])
    smart_p4 = np.mean([r['y4_p'] for r in smart])
    imp = (smart_p4 - fcfs_p4) / fcfs_p4 * 100
    print(f"\n  Smart vs FCFS: {imp:+.1f}%")
    print(f"  Target achievement: {smart_p4/64*100:.0f}%")
