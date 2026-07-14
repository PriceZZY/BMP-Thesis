import pathlib
"""
Test run: 3 strategies comparison.
FCFS / Naive Hotspot / Smart Hotspot
"""
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from model.environment import ThamesEnvironment
from model.subsidy_strategies import FirstComeFirstServed, HotspotPriority, SmartHotspot
from model.simulation import run_single_simulation

_REPO = pathlib.Path(__file__).resolve().parents[2]

print("=" * 60)
print("ABM TEST RUN - 3 STRATEGIES")
print("=" * 60)

print("\nLoading environment...")
env = ThamesEnvironment(stochastic=False, seed=42)
summary = env.summary()
metrics = env.detailed_metrics()
print(f"\nInitial state:")
print(f"  Farms: {summary['total_farms']}")
print(f"  Total area: {summary['total_area_ha']:.0f} ha ({summary['total_area_ha']*2.471:.0f} acres)")
print(f"  Pre-adopted Type A: {summary['adopted_a']} ({summary['adoption_rate']:.0%})")
print(f"  Base P load: {metrics['base_load_tonnes']:.1f} tonnes/year")
print(f"  Target reduction: {metrics['target_tonnes']:.0f} tonnes/year")

strategies = {
    'FCFS (current policy)': FirstComeFirstServed(subsidy_a=30, subsidy_b=30, seed=42),
    'Naive Hotspot ($50/$30 premium)': HotspotPriority(high_subsidy=50, med_subsidy=30, seed=42),
    'Smart Hotspot (same price, spatial order)': SmartHotspot(subsidy_a=30, subsidy_b=30, seed=42),
}

results = {}

for name, strategy in strategies.items():
    print(f"\n{'=' * 60}")
    print(f"SCENARIO: {name}")
    print(f"{'=' * 60}")
    run = run_single_simulation(env, strategy, years=4, seed=42, verbose=True)

    y4 = run[-1]
    total_cost = sum(r['total_cost'] for r in run)
    results[name] = {
        'p_reduction': y4['p_reduction_tonnes'],
        'additional_reduction': y4.get('additional_reduction_tonnes', 0),
        'bioavailable_reduction': y4.get('bioavailable_reduction_tonnes', 0),
        'target_pct': y4.get('target_achievement_pct', 0),
        'additional_target_pct': y4.get('additional_target_pct', 0),
        'total_cost': total_cost,
        'cost_per_kg': total_cost / max(y4['p_reduction_tonnes'] * 1000, 1),
        'adoption_rate': y4['adoption_rate'],
        'cap_blocked_y4': y4.get('cap_blocked', 0),
        'budget_util_y1': run[0].get('budget_utilization', 0),
    }

# Comparison
print(f"\n{'=' * 60}")
print(f"FINAL COMPARISON (Year 4)")
print(f"{'=' * 60}")

print(f"\n{'Strategy':<45} {'P(t)':<7} {'Add(t)':<7} {'BioP(t)':<8} "
      f"{'Tgt%':<6} {'AddTgt%':<8} {'$M':<6} {'$/kg':<6}")
print("-" * 100)

fcfs_p = results['FCFS (current policy)']['p_reduction']

for name, r in results.items():
    imp = (r['p_reduction'] - fcfs_p) / fcfs_p * 100 if fcfs_p > 0 else 0
    tag = f"({imp:+.0f}%)" if name != 'FCFS (current policy)' else "(base)"
    print(f"  {name:<43} {r['p_reduction']:<7.1f} {r['additional_reduction']:<7.1f} "
          f"{r['bioavailable_reduction']:<8.1f} {r['target_pct']:<6.0f} "
          f"{r['additional_target_pct']:<8.0f} {r['total_cost']/1e6:<6.1f} "
          f"{r['cost_per_kg']:<6.0f} {tag}")

print("\nTest complete!")
