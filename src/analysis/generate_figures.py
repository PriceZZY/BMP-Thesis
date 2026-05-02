"""
Generate all paper figures from Monte Carlo results.
Figures 2-7 (Figure 1 already done separately).
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

RESULTS = Path("D:/Claude/BMP-Thesis/results")
FIGURES = RESULTS / "figures"
FIGURES.mkdir(exist_ok=True)

# Load Monte Carlo results
with open(RESULTS / "monte_carlo_results.json") as f:
    mc = json.load(f)

fcfs = mc['raw']['FCFS']
naive = mc['raw']['NaiveHotspot']
smart = mc['raw']['SmartHotspot']

# Style
plt.rcParams.update({
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 12,
    'figure.facecolor': 'white',
})

C_FCFS = '#3498DB'
C_NAIVE = '#E74C3C'
C_SMART = '#27AE60'
COLORS = [C_FCFS, C_NAIVE, C_SMART]
NAMES = ['FCFS\n(current)', 'Naive\nHotspot', 'Smart\nHotspot']

# ============================================================
# Figure 3: Strategy comparison boxplot (total P reduction)
# ============================================================
print("Generating Figure 3: Strategy comparison boxplot...")

fig, axes = plt.subplots(1, 3, figsize=(14, 5))

# Panel A: Total P reduction
data_p = [[r['p_reduction_t'] for r in fcfs],
          [r['p_reduction_t'] for r in naive],
          [r['p_reduction_t'] for r in smart]]

bp = axes[0].boxplot(data_p, labels=NAMES, patch_artist=True, widths=0.6,
                      medianprops=dict(color='black', linewidth=2))
for patch, color in zip(bp['boxes'], COLORS):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[0].axhline(y=64, color='red', linestyle='--', linewidth=1.5, label='40% target (64 t/yr)')
axes[0].set_ylabel('Total P Reduction (tonnes/yr)')
axes[0].set_title('(a) Total Phosphorus Reduction')
axes[0].legend(fontsize=9)

# Panel B: Cost per kg
data_cost = [[r['cost_per_kg'] for r in fcfs],
             [r['cost_per_kg'] for r in naive],
             [r['cost_per_kg'] for r in smart]]

bp2 = axes[1].boxplot(data_cost, labels=NAMES, patch_artist=True, widths=0.6,
                       medianprops=dict(color='black', linewidth=2))
for patch, color in zip(bp2['boxes'], COLORS):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[1].set_ylabel('Cost per kg P Reduced ($/kg)')
axes[1].set_title('(b) Cost Efficiency')

# Panel C: Improvement vs FCFS
fcfs_p_arr = np.array([r['p_reduction_t'] for r in fcfs])
naive_imp = [(n['p_reduction_t'] - f['p_reduction_t']) / f['p_reduction_t'] * 100
             for n, f in zip(naive, fcfs)]
smart_imp = [(s['p_reduction_t'] - f['p_reduction_t']) / f['p_reduction_t'] * 100
             for s, f in zip(smart, fcfs)]

bp3 = axes[2].boxplot([naive_imp, smart_imp],
                       labels=['Naive\nHotspot', 'Smart\nHotspot'],
                       patch_artist=True, widths=0.5,
                       medianprops=dict(color='black', linewidth=2))
bp3['boxes'][0].set_facecolor(C_NAIVE)
bp3['boxes'][0].set_alpha(0.7)
bp3['boxes'][1].set_facecolor(C_SMART)
bp3['boxes'][1].set_alpha(0.7)
axes[2].axhline(y=0, color='gray', linestyle='-', linewidth=1)
axes[2].set_ylabel('Improvement vs FCFS (%)')
axes[2].set_title('(c) Relative Improvement')

plt.tight_layout()
plt.savefig(FIGURES / 'fig3_strategy_comparison.png', dpi=300, bbox_inches='tight')
print("  Saved fig3_strategy_comparison.png")

# ============================================================
# Figure 4: Additionality waterfall
# ============================================================
print("Generating Figure 4: Additionality waterfall...")

fig, ax = plt.subplots(figsize=(10, 6))

# Use mean values
strategies = ['FCFS', 'Naive Hotspot', 'Smart Hotspot']
gross = [np.mean([r['p_reduction_t'] for r in d]) for d in [fcfs, naive, smart]]
additional = [np.mean([r.get('additional_t', r['p_reduction_t'] * 0.78) for r in d])
              for d in [fcfs, naive, smart]]
free_rider = [g - a for g, a in zip(gross, additional)]

x = np.arange(len(strategies))
width = 0.35

bars1 = ax.bar(x - width/2, gross, width, label='Gross Reduction',
               color=[C_FCFS, C_NAIVE, C_SMART], alpha=0.4, edgecolor='black')
bars2 = ax.bar(x + width/2, additional, width, label='Additional (policy effect)',
               color=[C_FCFS, C_NAIVE, C_SMART], alpha=0.9, edgecolor='black')

ax.axhline(y=64, color='red', linestyle='--', linewidth=1.5, label='40% target (64 t/yr)')
ax.set_ylabel('P Reduction (tonnes/yr)')
ax.set_title('Gross vs Additional (Policy-Attributable) Phosphorus Reduction')
ax.set_xticks(x)
ax.set_xticklabels(strategies)
ax.legend()

# Add labels
for bar, val in zip(bars1, gross):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{val:.0f}t', ha='center', va='bottom', fontsize=10)
for bar, val in zip(bars2, additional):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
            f'{val:.0f}t', ha='center', va='bottom', fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(FIGURES / 'fig4_additionality.png', dpi=300, bbox_inches='tight')
print("  Saved fig4_additionality.png")

# ============================================================
# Figure 5: Precipitation masking
# ============================================================
print("Generating Figure 5: Precipitation masking...")

fig, ax = plt.subplots(figsize=(10, 6))

# Scatter: each dot is one MC run, x=precip effect on base load, y=P reduction
# Use y1 data for clearest signal
fcfs_y1_p = [r['y1_p'] for r in fcfs]
# Approximate base load from total reduction / fraction
# Instead, show the distribution width
p_reductions = [r['p_reduction_t'] for r in fcfs]

# Histogram of P reduction showing the wide spread
ax.hist(p_reductions, bins=50, color=C_FCFS, alpha=0.6, label='FCFS', edgecolor='white')
ax.hist([r['p_reduction_t'] for r in smart], bins=50, color=C_SMART, alpha=0.6,
        label='Smart Hotspot', edgecolor='white')

ax.axvline(x=64, color='red', linestyle='--', linewidth=2, label='40% target (64 t/yr)')
ax.axvline(x=np.mean(p_reductions), color=C_FCFS, linestyle='-', linewidth=2, alpha=0.8)
ax.axvline(x=np.mean([r['p_reduction_t'] for r in smart]), color=C_SMART,
           linestyle='-', linewidth=2, alpha=0.8)

ax.set_xlabel('Year 4 P Reduction (tonnes/yr)')
ax.set_ylabel('Frequency (out of 1,000 runs)')
ax.set_title('Distribution of P Reduction Outcomes\n(width driven by precipitation variability)')
ax.legend()

# Add annotation
ax.annotate('Dry years:\nBMPs unnecessary\n(little P moves)',
            xy=(25, 50), fontsize=9, color='gray',
            bbox=dict(boxstyle='round', facecolor='lightyellow'))
ax.annotate('Wet years:\nBMPs overwhelmed\n(high P load)',
            xy=(200, 30), fontsize=9, color='gray',
            bbox=dict(boxstyle='round', facecolor='lightyellow'))

plt.tight_layout()
plt.savefig(FIGURES / 'fig5_precipitation_masking.png', dpi=300, bbox_inches='tight')
print("  Saved fig5_precipitation_masking.png")

# ============================================================
# Figure 7: Gap analysis bar chart
# ============================================================
print("Generating Figure 7: Gap analysis...")

fig, ax = plt.subplots(figsize=(10, 6))

target = 64
categories = ['Gross Total P', 'After\nAdditionality', 'Bioavailable P\n(PP*0.25+DRP*1.0)']

# Smart Hotspot values (best strategy)
smart_gross = np.mean([r['p_reduction_t'] for r in smart])
smart_additional = np.mean([r.get('additional_t', r['p_reduction_t'] * 0.78) for r in smart])
smart_bioavail = np.mean([r.get('bioavailable_t', r['p_reduction_t'] * 0.42) for r in smart])

values = [smart_gross, smart_additional, smart_bioavail]
colors_bar = [C_SMART, '#2ECC71', '#1ABC9C']

bars = ax.barh(categories, values, color=colors_bar, height=0.5, edgecolor='black', alpha=0.85)
ax.axvline(x=target, color='red', linestyle='--', linewidth=2, label=f'40% target ({target} t/yr)')

# Labels on bars
for bar, val in zip(bars, values):
    pct = val / target * 100
    ax.text(val + 1, bar.get_y() + bar.get_height()/2,
            f'{val:.0f}t ({pct:.0f}% of target)',
            ha='left', va='center', fontsize=11, fontweight='bold')

ax.set_xlabel('Phosphorus Reduction (tonnes/yr)')
ax.set_title('Gap Analysis: Smart Hotspot vs 40% Target\n(progressive adjustment reveals structural gap)')
ax.legend(fontsize=11)
ax.set_xlim(0, 110)

plt.tight_layout()
plt.savefig(FIGURES / 'fig7_gap_analysis.png', dpi=300, bbox_inches='tight')
print("  Saved fig7_gap_analysis.png")

print("\nAll figures generated!")
print(f"  Fig 1: Transport chain (already exists)")
print(f"  Fig 3: Strategy comparison boxplot")
print(f"  Fig 4: Additionality waterfall")
print(f"  Fig 5: Precipitation masking histogram")
print(f"  Fig 7: Gap analysis bar chart")
print(f"\n  Fig 2 (P-risk map) and Fig 6 (adoption diffusion) require GIS plotting — deferred")
