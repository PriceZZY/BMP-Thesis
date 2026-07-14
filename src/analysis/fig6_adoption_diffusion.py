import pathlib
"""
Figure 6: Adoption diffusion over 4 years under Smart Hotspot.
4-panel map showing spatial spread of BMP adoption via peer effects.
"""
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from pathlib import Path

from model.environment import ThamesEnvironment
from model.subsidy_strategies import SmartHotspot
from model.simulation import simulate_program, PARTICIPATION_RATES

_REPO = pathlib.Path(__file__).resolve().parents[2]

PROCESSED = (_REPO / "data/processed")
RAW = (_REPO / "data/raw")
FIGURES = (_REPO / "results/figures")

# Load spatial data for plotting
print("Loading spatial data...")
fields_gdf = gpd.read_file(PROCESSED / "field_agents_upper_thames.gpkg").to_crs("EPSG:32617")
boundary = gpd.read_file(PROCESSED / "upper_thames_boundary.gpkg").to_crs("EPSG:32617")
rivers = gpd.read_file(RAW / "hydro_network" / "ohn_watercourse.geojson").to_crs("EPSG:32617")
rivers = gpd.clip(rivers, boundary)

# Load ABM environment
print("Loading ABM environment...")
env = ThamesEnvironment(stochastic=False, seed=42)

# Run Smart Hotspot WITH participation filter (constrained scenario — matches
# the paper's central finding in Section 5.2–5.3). Without the filter, Year 4
# adoption would climb past 60% of fields, inconsistent with Table 3.
strategy = SmartHotspot(subsidy_a=30, subsidy_b=30, seed=42)
env.reset()

# Apply the two-stage participation filter (same mechanism as run_single_simulation)
part_rng = np.random.RandomState(42 + 50000)
for farm in env.farms:
    farm._type_b_spent = 0
    farm.is_additional = False
    rate = PARTICIPATION_RATES.get(farm.risk_level, 0.40)
    farm._will_participate = part_rng.random() < rate

env.rng = np.random.RandomState(42)

# Track adoption per year
yearly_adoption = {}  # year -> set of farm_ids that are adopted

# Record initial state (Year 0)
yearly_adoption[0] = set(f.farm_id for f in env.farms if f.adopted)
print(f"  Year 0 (initial): {len(yearly_adoption[0])} adopted")

# Run 4 years
rng = np.random.RandomState(42)
for year in range(1, 5):
    env.current_precip_multiplier = 1.0  # deterministic for visualization
    total_cost = 0
    farm_order = strategy.order_farms(env.farms)

    for farm in farm_order:
        from model.simulation import FARM_TOTAL_CAP, TYPE_B_CAP, COMBO_BONUS_PER_ACRE
        from model.adoption_function import adoption_probability

        # Enforce participation filter
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
            effective = actual_cost / max(farm.area_acres, 1)
            if effective < 5:
                continue
            offer = {'type': offer['type'], 'subsidy_per_acre': effective, 'total_cost': actual_cost}

        prob = adoption_probability(farm, offer, rng=rng)
        if rng.random() < prob:
            farm.adopt(offer['type'], year)
            total_cost += actual_cost
            farm.total_subsidy_received += actual_cost

        if total_cost >= 4_350_000:
            break

    yearly_adoption[year] = set(f.farm_id for f in env.farms if f.adopted)
    new = len(yearly_adoption[year]) - len(yearly_adoption.get(year-1, set()))
    print(f"  Year {year}: {len(yearly_adoption[year])} adopted (+{new} new)")

# Plot 4-panel figure
print("Generating Figure 6...")
fig, axes = plt.subplots(2, 2, figsize=(16, 14))

C_NOT_ADOPTED = '#E8E8E8'
C_PRE_ADOPTED = '#85C1E9'  # light blue for initial 27%
C_NEW_ADOPTED = '#E74C3C'  # red for new this year
C_PREV_ADOPTED = '#27AE60'  # green for previously adopted

for idx, year in enumerate([1, 2, 3, 4]):
    ax = axes[idx // 2][idx % 2]

    pre_adopted = yearly_adoption[0]
    prev_adopted = yearly_adoption.get(year - 1, set()) - pre_adopted
    new_adopted = yearly_adoption[year] - yearly_adoption.get(year - 1, set())
    not_adopted = set(range(len(env.farms))) - yearly_adoption[year]

    # Assign colors
    colors = []
    for i in range(len(fields_gdf)):
        if i in new_adopted:
            colors.append(C_NEW_ADOPTED)
        elif i in prev_adopted:
            colors.append(C_PREV_ADOPTED)
        elif i in pre_adopted:
            colors.append(C_PRE_ADOPTED)
        else:
            colors.append(C_NOT_ADOPTED)

    # Plot
    boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=1.5, zorder=3)
    fields_gdf.plot(ax=ax, color=colors, edgecolor='none', alpha=0.8, zorder=1)
    rivers.plot(ax=ax, color='#3498DB', linewidth=0.3, alpha=0.4, zorder=2)

    adopted_total = len(yearly_adoption[year])
    rate = adopted_total / len(env.farms) * 100
    new_count = len(new_adopted)

    ax.set_title(f'Year {year}: {adopted_total} adopted ({rate:.0f}%), +{new_count} new',
                 fontsize=12, fontweight='bold')
    ax.set_xticks([])
    ax.set_yticks([])

# Shared legend
legend_elements = [
    Line2D([0], [0], marker='s', color='w', markerfacecolor=C_PRE_ADOPTED,
           markersize=12, label='Pre-adopted (Year 0, 27%)'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor=C_PREV_ADOPTED,
           markersize=12, label='Previously adopted'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor=C_NEW_ADOPTED,
           markersize=12, label='Newly adopted this year'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor=C_NOT_ADOPTED,
           markersize=12, label='Not adopted'),
]
fig.legend(handles=legend_elements, loc='lower center', ncol=4, fontsize=11,
           framealpha=0.9, edgecolor='gray', bbox_to_anchor=(0.5, -0.01))

fig.suptitle('Spatial Diffusion of BMP Adoption over 4 Years\n'
             'under Smart Hotspot + Participation Filter (constrained scenario)',
             fontsize=14, fontweight='bold', y=1.01)

plt.tight_layout()
plt.savefig(FIGURES / 'fig6_adoption_diffusion.png', dpi=200, bbox_inches='tight')
print("Saved fig6_adoption_diffusion.png")
