import pathlib
"""
Master figure generator (v2) — produces Figs 3, 4, 5, 7 aligned with
draft_FINAL.md v2 post-citation-audit.

Changes vs v1 (pre-2026-04 fix):
- All 4 strategies (FCFS, NaiveHotspot, SmartHotspot, EfficiencyPricing) shown
  in Figs 3 and 4.
- Fig 5 target-line relabeled to avoid the "317 t/yr" absolute-load framing;
  signal value updated to the constrained FCFS mean (~43 t/yr) to match the
  paper's central finding.
- Fig 7 uses FCFS (Section 5.5's chosen strategy), not Smart Hotspot.
- Additionality/bioavailability multipliers retained as approximations; values
  match paper's calibration-adjusted ~14 t/yr bioavailable figure conceptually.
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

_REPO = pathlib.Path(__file__).resolve().parents[2]

RESULTS = (_REPO / "results")
FIGURES = RESULTS / "figures"

with open(RESULTS / "monte_carlo_results.json") as f:
    mc = json.load(f)

fcfs = mc['raw']['FCFS']
naive = mc['raw']['NaiveHotspot']
smart = mc['raw']['SmartHotspot']
effic = mc['raw']['EfficiencyPricing']

# Colors and names (4 strategies)
C_FCFS = '#3498DB'
C_NAIVE = '#E74C3C'
C_SMART = '#27AE60'
C_EFFIC = '#8E44AD'
COLORS4 = [C_FCFS, C_NAIVE, C_SMART, C_EFFIC]
NAMES4 = ['FCFS\n(current)', 'Naive\nHotspot', 'Smart\nHotspot', 'Efficiency\nPricing']

plt.rcParams.update({'font.size': 11, 'axes.titlesize': 13, 'axes.labelsize': 12,
                     'figure.facecolor': 'white'})


# ============================================================
# FIG 3: Strategy comparison — 4 strategies, 3 panels
# ============================================================
print("Generating Figure 3: Strategy comparison (4 strategies)...")

fig, axes = plt.subplots(1, 3, figsize=(15, 5.2))

# Panel A: Total P Reduction
data_p = [[r['p_reduction_t'] for r in d] for d in [fcfs, naive, smart, effic]]
bp = axes[0].boxplot(data_p, tick_labels=NAMES4, patch_artist=True, widths=0.6,
                     medianprops=dict(color='black', linewidth=2))
for patch, color in zip(bp['boxes'], COLORS4):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[0].axhline(y=64, color='red', linestyle='--', linewidth=1.5,
                label='40% target (64 t/yr)')
axes[0].set_ylabel('Total P Reduction (tonnes/yr)')
axes[0].set_title('(a) Total Phosphorus Reduction')
axes[0].legend(fontsize=9)

# Panel B: Cost per kg (capped at $1500 — Efficiency has long tail)
CAP = 1500
data_cost = [[min(r['cost_per_kg'], CAP) for r in d] for d in [fcfs, naive, smart, effic]]
bp2 = axes[1].boxplot(data_cost, tick_labels=NAMES4, patch_artist=True, widths=0.6,
                      medianprops=dict(color='black', linewidth=2))
for patch, color in zip(bp2['boxes'], COLORS4):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[1].set_ylabel('Cost per kg P Reduced ($/kg)')
axes[1].set_title(f'(b) Cost Efficiency (capped at ${CAP})')
axes[1].set_ylim(0, CAP + 50)

# Panel C: Improvement vs FCFS (%)
def pct_impr(alt, base):
    return [(a['p_reduction_t'] - b['p_reduction_t']) / b['p_reduction_t'] * 100
            for a, b in zip(alt, base)]

imp_naive = pct_impr(naive, fcfs)
imp_smart = pct_impr(smart, fcfs)
imp_effic = pct_impr(effic, fcfs)

bp3 = axes[2].boxplot(
    [imp_naive, imp_smart, imp_effic],
    tick_labels=['Naive\nHotspot', 'Smart\nHotspot', 'Efficiency\nPricing'],
    patch_artist=True, widths=0.5,
    medianprops=dict(color='black', linewidth=2))
for patch, color in zip(bp3['boxes'], [C_NAIVE, C_SMART, C_EFFIC]):
    patch.set_facecolor(color)
    patch.set_alpha(0.7)
axes[2].axhline(y=0, color='gray', linestyle='-', linewidth=1)
axes[2].set_ylabel('Improvement vs FCFS (%)')
axes[2].set_title('(c) Relative Improvement')

plt.tight_layout()
plt.savefig(FIGURES / 'fig3_strategy_comparison.png', dpi=300, bbox_inches='tight')
print("  Saved fig3_strategy_comparison.png")


# ============================================================
# FIG 4: Additionality waterfall — 4 strategies
# Approx. multipliers:
#   additional ≈ gross × 0.78 (tracks paper's "20-25% would have occurred anyway"
#   and Claassen-range averages)
# Legend placed at upper-right to avoid bar-label occlusion.
# ============================================================
print("Generating Figure 4: Additionality (4 strategies)...")

ADDITIONAL_MULT = 0.78

fig, ax = plt.subplots(figsize=(11, 6))
strategies = ['FCFS', 'Naive Hotspot', 'Smart Hotspot', 'Efficiency Pricing']

gross = [np.mean([r['p_reduction_t'] for r in d]) for d in [fcfs, naive, smart, effic]]
additional = [g * ADDITIONAL_MULT for g in gross]

x = np.arange(len(strategies))
width = 0.38

bars1 = ax.bar(x - width / 2, gross, width,
               color=COLORS4, alpha=0.4, edgecolor='black')
bars2 = ax.bar(x + width / 2, additional, width,
               color=COLORS4, alpha=0.9, edgecolor='black')

ax.axhline(y=64, color='red', linestyle='--', linewidth=1.5,
           label='40% target (64 t/yr)')

ax.set_ylabel('P Reduction (tonnes/yr)')
ax.set_title('Gross vs Additional (Policy-Attributable) Phosphorus Reduction\n'
             '(constrained scenario: participation filter ON)')
ax.set_xticks(x)
ax.set_xticklabels(strategies)

# Legend clarifies bar-pair encoding: light = gross, dark = additional.
# Colors distinguish strategies only — see x-axis labels.
from matplotlib.patches import Patch
legend_handles = [
    Patch(facecolor='#7F7F7F', alpha=0.4, edgecolor='black', label='Light bar: Gross reduction'),
    Patch(facecolor='#3F3F3F', alpha=0.9, edgecolor='black', label='Dark bar: Additional (policy-attributable)'),
    plt.Line2D([0], [0], color='red', linestyle='--', linewidth=1.5, label='40% target (64 t/yr)'),
]
ax.legend(handles=legend_handles, loc='upper right', framealpha=0.95,
          title='Colors distinguish strategies (see x-axis)', title_fontsize=9)

# Bar value labels
for bar, val in zip(bars1, gross):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
            f'{val:.0f}t', ha='center', va='bottom', fontsize=10)
for bar, val in zip(bars2, additional):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
            f'{val:.0f}t', ha='center', va='bottom', fontsize=10, fontweight='bold')

# Set y-limit so both the 64 t/yr target line and bar labels are visible
ax.set_ylim(0, max(64, max(gross)) * 1.45)

plt.tight_layout()
plt.savefig(FIGURES / 'fig4_additionality.png', dpi=300, bbox_inches='tight')
print("  Saved fig4_additionality.png")


# ============================================================
# FIG 5: Precipitation masking — signal vs noise
# Fixes: use constrained FCFS mean for signal (~43 t/yr), reframe target line
# so the 40% metric is expressed as reduction (label makes both framings explicit).
# ============================================================
print("Generating Figure 5: Precipitation masking (signal vs noise)...")

fig, ax = plt.subplots(figsize=(12, 6))

rng = np.random.RandomState(42)
n_years = 20
precip_multipliers = rng.lognormal(-0.18, 0.6, n_years)

# Baseline Thames P load used for illustration (long-term mean ~300 t/yr per paper L109;
# kept near historical mean of the loading series for visual clarity)
base_load_mean = 300.0
total_loads = base_load_mean * precip_multipliers

# Constrained FCFS signal: mean ≈ 43 t/yr (paper Table 3)
bmp_reduction_mean = 43.0
bmp_reductions = bmp_reduction_mean * precip_multipliers * (1 + rng.normal(0, 0.1, n_years))
bmp_reductions = np.clip(bmp_reductions, 0, None)
net_loads = total_loads - bmp_reductions

years = np.arange(2005, 2005 + n_years)

ax.fill_between(years, total_loads, net_loads, alpha=0.18, color=C_FCFS,
                label='BMP reduction band (signal)')
ax.plot(years, total_loads, 'o-', color='#2C3E50', linewidth=2, markersize=6,
        label='Total P load without BMP', zorder=3)
ax.plot(years, net_loads, 's--', color=C_FCFS, linewidth=2, markersize=5,
        label='Total P load with BMP (FCFS)', zorder=3)

# Target line removed: this figure is about BMP signal vs precipitation noise,
# not target-achievement. Plotting a 40%-target line here was misleading because
# the residual load implied by baseline × 0.60 is a 120 t/yr reduction (not
# the 64 t/yr target derived from the 212 t/yr Canadian share). Target
# achievement is handled by Fig 7 (Gap Analysis) and Fig 3 (Table 3).

# Annotations: wet/dry extremes
wet_idx = int(np.argmax(precip_multipliers))
dry_idx = int(np.argmin(precip_multipliers))

wet_load = total_loads[wet_idx]
dry_load = total_loads[dry_idx]
ymax_axis = max(total_loads) * 1.18  # matches ylim below

# Place wet-year annotation below the point so it stays in-axis
ax.annotate(f'Wet year: {wet_load:.0f} t\n'
            f'BMP reduces {bmp_reductions[wet_idx]:.0f} t\n'
            f'({bmp_reductions[wet_idx] / wet_load * 100:.0f}% of load)',
            xy=(years[wet_idx], wet_load),
            xytext=(years[wet_idx] - 5.5, wet_load * 0.75),
            fontsize=9, arrowprops=dict(arrowstyle='->', color='gray'),
            bbox=dict(boxstyle='round', facecolor='lightyellow'))

ax.annotate(f'Dry year: {dry_load:.0f} t\n'
            f'BMP reduces {bmp_reductions[dry_idx]:.0f} t',
            xy=(years[dry_idx], dry_load),
            xytext=(years[dry_idx] + 1.5, dry_load + 80),
            fontsize=9, arrowprops=dict(arrowstyle='->', color='gray'),
            bbox=dict(boxstyle='round', facecolor='lightyellow'))

# Signal-to-noise summary box
signal = bmp_reduction_mean
noise = np.std(total_loads)
ax.text(0.02, 0.97,
        f'Signal (BMP mean reduction): ~{signal:.0f} t/yr\n'
        f'Noise (precip-driven SD): {noise:.0f} t/yr\n'
        f'Signal-to-noise ratio: {signal / noise:.2f}',
        transform=ax.transAxes, fontsize=10, va='top',
        bbox=dict(boxstyle='round', facecolor='white', edgecolor='gray', alpha=0.9))

ax.set_xlabel('Year (illustrative 20-year sequence)')
ax.set_ylabel('Phosphorus Load (tonnes/yr)')
ax.set_title('BMP Signal vs Precipitation Noise in the Thames River Watershed')
ax.legend(loc='upper right', fontsize=9)
ax.set_ylim(0, max(total_loads) * 1.18)
# Integer year ticks (every 2 years) — avoid matplotlib's default decimal formatting
ax.set_xticks(np.arange(years[0], years[-1] + 1, 2))

plt.tight_layout()
plt.savefig(FIGURES / 'fig5_precipitation_masking.png', dpi=300, bbox_inches='tight')
print("  Saved fig5_precipitation_masking.png")


# ============================================================
# FIG 7: Gap analysis — FCFS (Section 5.5) with structural-gap annotation
# ============================================================
print("Generating Figure 7: Gap analysis (FCFS)...")

ADDITIONAL_MULT_GAP = 0.78   # weighted avg of (1 − baseline adoption prob) across risk strata:
                             #   Low 0.60, Medium 0.80, High 0.90; see §2.10
BIOAVAIL_MULT_GAP = 0.40     # PP(0.80)×0.25 + DRP(0.20)×1.0 = 0.40, matches §2.1 derivation exactly

fig, ax = plt.subplots(figsize=(10, 6))

target = 64
categories = ['Gross Total P', 'After\nAdditionality', 'Bioavailable P\n(PP×0.25 + DRP×1.0)']

fcfs_gross = np.mean([r['p_reduction_t'] for r in fcfs])
fcfs_additional = fcfs_gross * ADDITIONAL_MULT_GAP
fcfs_bioavail = fcfs_gross * BIOAVAIL_MULT_GAP

values = [fcfs_gross, fcfs_additional, fcfs_bioavail]
colors_bar = [C_FCFS, '#5DADE2', '#AED6F1']

bars = ax.barh(categories, values, color=colors_bar, height=0.5,
               edgecolor='black', alpha=0.9)
ax.axvline(x=target, color='red', linestyle='--', linewidth=2,
           label=f'40% target ({target} t/yr)')

for bar, val in zip(bars, values):
    pct = val / target * 100
    ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
            f'{val:.0f}t ({pct:.0f}% of target)',
            ha='left', va='center', fontsize=11, fontweight='bold')

# Structural gap annotation — arrow points at the Bioavailable P bar
# (index 2, the top bar in barh order) since the gap is measured from
# that bar (smallest) to the target line.
gap = target - fcfs_bioavail
ax.annotate(f'Structural gap:\n{gap:.0f}t ({gap / target * 100:.0f}% of target\nremains unmet)',
            xy=(fcfs_bioavail, 2),
            xytext=((fcfs_bioavail + target) / 2, 2.55),
            fontsize=11, fontweight='bold', color='red', ha='center',
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            bbox=dict(boxstyle='round', facecolor='#FADBD8', edgecolor='red'))

ax.set_xlabel('Phosphorus Reduction (tonnes/yr)')
ax.set_title('Gap Analysis: FCFS vs 40% Target\n'
             '(three independent adjustments reveal structural gap)')
# Footnote clarifying each bar is a separate adjustment off gross, not a cascade
ax.text(0.01, -0.13,
        'Each adjustment applied independently to gross reduction (not compounded): '
        'additionality factor = gross × 0.78 (weighted avg of 1 − baseline adoption '
        'probability across risk strata, see §2.10); bioavailable factor = gross × 0.40 '
        '(PP×0.25 + DRP×1.0 under the 80:20 partitioning, see §2.1).',
        transform=ax.transAxes, ha='left', va='top', fontsize=8.5,
        style='italic', color='#555555', wrap=True)
ax.legend(fontsize=11, loc='upper right')
ax.set_xlim(0, max(target, fcfs_gross) * 1.35)
ax.set_ylim(-0.7, 3.1)

plt.tight_layout()
plt.savefig(FIGURES / 'fig7_gap_analysis.png', dpi=300, bbox_inches='tight')
print("  Saved fig7_gap_analysis.png")


print("\nAll figures (3, 4, 5, 7) regenerated for v2.")
