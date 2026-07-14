import pathlib
"""
Figure 8: Tornado chart — sensitivity of Smart Hotspot improvement to each parameter.
"""
import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

_REPO = pathlib.Path(__file__).resolve().parents[2]

RESULTS = (_REPO / "results")
FIGURES = RESULTS / "figures"

with open(RESULTS / "sensitivity_oat_results.json") as f:
    data = json.load(f)

# Extract improvement range for each parameter
params = []
for name, info in data.items():
    imps = [r['improvement_pct'] for r in info['results']]
    default_imp = None
    for r in info['results']:
        if abs(r['value'] - info['default']) < 0.001:
            default_imp = r['improvement_pct']
    params.append({
        'name': info['label'],
        'min_imp': min(imps),
        'max_imp': max(imps),
        'default_imp': default_imp or np.mean(imps),
        'range': max(imps) - min(imps),
    })

# Sort by range (largest influence at top)
params.sort(key=lambda x: x['range'])

fig, ax = plt.subplots(figsize=(12, 7))

y_pos = np.arange(len(params))
default = params[0]['default_imp']  # All defaults should be ~5.8%

# Find the common default value
for p in params:
    if p['name'] == 'Peer Effect Coefficient':
        default = p['default_imp']

colors_low = '#3498DB'
colors_high = '#E74C3C'

for i, p in enumerate(params):
    # Bar from min to default
    ax.barh(i, p['default_imp'] - p['min_imp'],
            left=p['min_imp'], height=0.6,
            color=colors_low, alpha=0.7, edgecolor='white')
    # Bar from default to max
    ax.barh(i, p['max_imp'] - p['default_imp'],
            left=p['default_imp'], height=0.6,
            color=colors_high, alpha=0.7, edgecolor='white')

    # Labels at ends
    if p['range'] > 0.5:
        ax.text(p['min_imp'] - 0.3, i, f"{p['min_imp']:.1f}%",
                ha='right', va='center', fontsize=9)
        ax.text(p['max_imp'] + 0.3, i, f"{p['max_imp']:.1f}%",
                ha='left', va='center', fontsize=9)

# Default line
ax.axvline(x=5.8, color='black', linestyle='--', linewidth=1.5,
           label=f'Default ({5.8:.1f}%)')

ax.set_yticks(y_pos)
ax.set_yticklabels([p['name'] for p in params], fontsize=10)
ax.set_xlabel('Smart Hotspot Improvement over FCFS (%)', fontsize=12)
ax.set_title('Parameter Sensitivity — Unconstrained Scenario\n'
             '(participation filter OFF; peer effect is the sole significant driver)',
             fontsize=13, fontweight='bold')

# Annotation for peer effect
ax.annotate('Peer effect determines\nwhether spatial targeting\nmatters (+3% to +15%)',
            xy=(15.0, len(params)-1), xytext=(11, len(params)-2.5),
            fontsize=10, fontweight='bold', color='#E74C3C',
            arrowprops=dict(arrowstyle='->', color='#E74C3C', lw=2),
            bbox=dict(boxstyle='round', facecolor='#FADBD8', edgecolor='#E74C3C'))

# Note that peer-effect influence is neutralized under the participation filter
ax.text(0.98, 0.02,
        'Under the constrained scenario (participation filter ON, §3.6),\n'
        'peer-effect influence collapses — the participation constraint dominates\n'
        'adoption dynamics and Smart Hotspot underperforms FCFS (-1.6%, Table 3).',
        transform=ax.transAxes, ha='right', va='bottom', fontsize=9,
        style='italic', color='#555555',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#F8F9FA',
                  edgecolor='#95A5A6', linewidth=0.8))

ax.legend(fontsize=10, loc='upper left')
ax.set_xlim(-1, 18)

plt.tight_layout()
plt.savefig(FIGURES / 'fig8_sensitivity_tornado.png', dpi=300, bbox_inches='tight')
print("Saved fig8_sensitivity_tornado.png")
