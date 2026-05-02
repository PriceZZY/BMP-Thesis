"""
4-year dynamic BMP simulation with full transport chain.

Enhancements per PAPER_GUIDE:
- Annual precipitation variability (LogNormal)
- Additionality tracking (gross vs net policy effect)
- Bioavailable P metric
- Policy constraints ($75K cap, Type B cap, combo bonus)
"""

import numpy as np
from .adoption_function import adoption_probability

DEFAULT_ANNUAL_BUDGET = 4_350_000
FARM_TOTAL_CAP = 75_000
TYPE_B_CAP = 12_500
COMBO_BONUS_PER_ACRE = 10

# Participation filter: probability of engaging with program at all
# Inverse relationship: high-risk farms least likely to participate
PARTICIPATION_RATES = {
    'Low': 0.55,
    'Medium': 0.45,
    'High': 0.30,
}


def simulate_program(env, strategy, annual_budget=DEFAULT_ANNUAL_BUDGET,
                     years=4, seed=None, verbose=False):
    rng = np.random.RandomState(seed)
    yearly_results = []

    for year in range(1, years + 1):
        # P1: Sample precipitation for this year
        env.current_precip_multiplier = env.sample_precip_multiplier()

        total_cost = 0
        new_adoptions = 0
        new_adoption_acres = 0
        additional_adoptions = 0  # P1: additionality tracking
        cap_blocked = 0

        farm_order = strategy.order_farms(env.farms)

        for farm in farm_order:
            # Participation filter — applies to ALL strategies
            if not getattr(farm, '_will_participate', True):
                continue

            # Check $75K farm cap
            remaining_farm_cap = FARM_TOTAL_CAP - farm.total_subsidy_received
            if remaining_farm_cap <= 0:
                cap_blocked += 1
                continue

            # Get offer
            remaining_budget = annual_budget - total_cost
            offer = strategy.allocate(farm, remaining_budget)
            if offer['type'] == 'none':
                continue

            # Type B per-category cap
            type_b_spent = getattr(farm, '_type_b_spent', 0)
            if offer['type'] == 'type_b':
                if type_b_spent + offer['total_cost'] > TYPE_B_CAP:
                    cap_blocked += 1
                    continue
            elif offer['type'] == 'both':
                type_b_this = offer['total_cost'] * 0.5
                if type_b_spent + type_b_this > TYPE_B_CAP:
                    if not farm.has_type_a:
                        per_acre = offer['subsidy_per_acre'] / 2
                        offer = strategy._make_offer(farm, 'type_a', per_acre)
                    else:
                        cap_blocked += 1
                        continue

            # Enforce farm cap — reduce offer if needed
            actual_cost = min(offer['total_cost'], remaining_farm_cap, remaining_budget)
            if actual_cost < offer['total_cost']:
                effective_per_acre = actual_cost / max(farm.area_acres, 1)
                if effective_per_acre < 5:
                    cap_blocked += 1
                    continue
                offer = {
                    'type': offer['type'],
                    'subsidy_per_acre': effective_per_acre,
                    'total_cost': actual_cost
                }

            # Combo bonus
            is_combo = (
                offer['type'] == 'both' or
                (offer['type'] == 'type_a' and farm.has_type_b) or
                (offer['type'] == 'type_b' and farm.has_type_a)
            )
            combo_cost = 0
            if is_combo:
                combo_cost = COMBO_BONUS_PER_ACRE * farm.area_acres
                combo_cost = max(0, min(combo_cost,
                                        remaining_budget - actual_cost,
                                        remaining_farm_cap - actual_cost))

            # Farm decides
            prob = adoption_probability(farm, offer, rng=rng)

            if rng.random() < prob:
                total_payment = actual_cost + combo_cost
                farm.adopt(offer['type'], year)
                total_cost += total_payment
                farm.total_subsidy_received += total_payment

                # Type B tracking
                if offer['type'] == 'type_b':
                    farm._type_b_spent = type_b_spent + actual_cost
                elif offer['type'] == 'both':
                    farm._type_b_spent = type_b_spent + actual_cost * 0.5

                new_adoptions += 1
                new_adoption_acres += farm.area_acres

                # P1: Additionality check
                # Would this farm have adopted WITHOUT the subsidy?
                baseline_prob = farm.baseline_adoption_prob
                if rng.random() > baseline_prob:
                    # This adoption is ADDITIONAL (would not have happened without subsidy)
                    farm.is_additional = True
                    additional_adoptions += 1
                else:
                    # Free rider — would have adopted anyway
                    farm.is_additional = False

            if total_cost >= annual_budget:
                break

        # Year-end detailed metrics
        metrics = env.detailed_metrics(sample=not env.stochastic)
        summary = env.summary()

        result = {
            'year': year,
            'precip_multiplier': env.current_precip_multiplier,
            'new_adoptions': new_adoptions,
            'additional_adoptions': additional_adoptions,
            'free_rider_adoptions': new_adoptions - additional_adoptions,
            'new_adoption_acres': new_adoption_acres,
            'cap_blocked': cap_blocked,
            'total_adopted': summary['adopted_any'],
            'adoption_rate': summary['adoption_rate'],
            'adopted_type_a': summary['adopted_a'],
            'adopted_type_b': summary['adopted_b'],
            'adopted_both': summary['adopted_both'],
            'total_cost': total_cost,
            'cumulative_cost': total_cost + sum(r['total_cost'] for r in yearly_results),
            'budget_utilization': total_cost / annual_budget,
            # Total P metrics
            'p_reduction_tonnes': metrics['total_reduction_tonnes'],
            'base_load_tonnes': metrics['base_load_tonnes'],
            'current_load_tonnes': metrics['current_load_tonnes'],
            # Transport chain breakdown
            'pp_reduction_tonnes': metrics['pp_reduction_tonnes'],
            'drp_reduction_tonnes': metrics['drp_reduction_tonnes'],
            # P1: Bioavailable P
            'bioavailable_reduction_tonnes': metrics['bioavailable_reduction_tonnes'],
            # P1: Additionality
            'additional_reduction_tonnes': metrics['additional_reduction_tonnes'],
            # P2: Gap analysis
            'target_achievement_pct': metrics['target_achievement_pct'],
            'additional_target_pct': metrics['additional_target_pct'],
            'target_gap_tonnes': metrics['target_tonnes'] - metrics['total_reduction_tonnes'],
        }

        yearly_results.append(result)

        if verbose:
            print(f"  Year {year} (precip={env.current_precip_multiplier:.2f}): "
                  f"+{new_adoptions} adoptions ({additional_adoptions} additional), "
                  f"rate={result['adoption_rate']:.1%}, "
                  f"P={result['p_reduction_tonnes']:.1f}t "
                  f"(add={result['additional_reduction_tonnes']:.1f}t), "
                  f"bioP={result['bioavailable_reduction_tonnes']:.1f}t, "
                  f"target={result['target_achievement_pct']:.0f}%, "
                  f"cost=${total_cost:,.0f}")

    return yearly_results


def run_single_simulation(env, strategy, annual_budget=DEFAULT_ANNUAL_BUDGET,
                          years=4, seed=None, verbose=False):
    env.reset()
    # Assign participation willingness (same for ALL strategies — fair comparison)
    part_rng = np.random.RandomState(seed + 50000 if seed else None)
    for farm in env.farms:
        farm._type_b_spent = 0
        farm.is_additional = False
        rate = PARTICIPATION_RATES.get(farm.risk_level, 0.40)
        farm._will_participate = part_rng.random() < rate
    if seed is not None:
        env.rng = np.random.RandomState(seed)
    return simulate_program(env, strategy, annual_budget, years, seed, verbose)
