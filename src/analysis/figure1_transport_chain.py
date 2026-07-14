import pathlib
"""
Figure 1: Phosphorus Transport Chain Diagram
From field application to Lake Erie, with BMP intervention points.

v2 (2026-04): numbers reconciled with draft_FINAL.md (10% NAPI; P-Index
threshold framing; years-to-decade+ drawdown; PP 25-50% bioavailable per
Baker 2014), and layout reworked to eliminate Type-B/legacy-leak overlap.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

_REPO = pathlib.Path(__file__).resolve().parents[2]

fig, ax = plt.subplots(1, 1, figsize=(16, 10))
ax.set_xlim(0, 16)
ax.set_ylim(0, 10)
ax.axis('off')

# Colors
C_SOURCE = '#E74C3C'
C_PROCESS = '#3498DB'
C_BMP = '#27AE60'
C_LOSS = '#95A5A6'
C_ARROW = '#2C3E50'
C_WARNING = '#F39C12'
C_BIOAVAIL = '#8E44AD'


def draw_box(x, y, w, h, text, color, fontsize=9, bold=False):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                         facecolor=color, edgecolor='#2C3E50',
                         linewidth=1.5, alpha=0.85)
    ax.add_patch(box)
    weight = 'bold' if bold else 'normal'
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fontsize, fontweight=weight, color='white',
            wrap=True, linespacing=1.3)


def draw_arrow(x1, y1, x2, y2, label='', color=C_ARROW, label_dy=0.18,
               label_x=None):
    """Draw an arrow with an optional italic label.

    label_x overrides the default (arrow midpoint) x-position — use when
    the arrow crosses other boxes and the midpoint label would be occluded.
    """
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle='->', color=color, lw=2))
    if label:
        mx = label_x if label_x is not None else (x1 + x2) / 2
        my = (y1 + y2) / 2
        ax.text(mx, my + label_dy, label, ha='center', va='bottom',
                fontsize=7.5, color=color, style='italic')


def draw_bmp_box(x, y, w, h, text, fontsize=7.5):
    box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                         facecolor=C_BMP, edgecolor='#1E8449',
                         linewidth=1.5, alpha=0.9, linestyle='--')
    ax.add_patch(box)
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fontsize, fontweight='bold', color='white',
            linespacing=1.2)


def draw_leak(x, y, text, width=2.1):
    ax.text(x, y, text, ha='center', va='center', fontsize=7.5,
            color=C_WARNING, fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.35', facecolor='#FDF2E9',
                      edgecolor=C_WARNING, linewidth=1))


# === TITLE ===
ax.text(8, 9.6, 'Phosphorus Transport Chain: From Field to Lake Erie',
        ha='center', va='center', fontsize=14, fontweight='bold', color=C_ARROW)
ax.text(8, 9.25,
        'BMP intervention points (green dashed) and structural leaks (orange)',
        ha='center', va='center', fontsize=9, color=C_LOSS)

# === ROW 1: SOURCES (left-center) ===
# Moved sources left to open room on the right for Type B BMP + legacy-P leak
draw_box(0.5, 7.5, 3.0, 1.2,
         'CURRENT-YEAR P\nFertilizer + Manure\n~10% of NAPI\nreaches rivers',
         C_SOURCE, fontsize=8, bold=True)

draw_box(4.0, 7.5, 3.0, 1.2,
         'LEGACY SOIL P\nOlsen P > 30 mg/kg\ntriggers P-Index\n(years to decade+ drawdown)',
         C_SOURCE, fontsize=7.8, bold=True)

# === TYPE B BMP (top right, moved right of sources) ===
draw_bmp_box(11.8, 7.5, 3.7, 1.2,
             'TYPE B BMP\nSubsurface P placement\n& nutrient management\n-50 to -88% DRP in runoff; $20-50/acre',
             fontsize=7.6)

# Arrow: Type B reduces current-year application losses. Label_x = 9.5
# places the text in the empty band between LEGACY SOIL P (ends x=7.0) and
# TYPE B BMP (starts x=11.8) — otherwise the arrow-midpoint default (x=7.65)
# puts the "Redu-" prefix under the LEGACY box.
draw_arrow(11.8, 8.1, 3.5, 8.1, 'Reduces application loss', C_BMP, label_x=9.5)

# Legacy-P structural leak: placed BELOW sources (y=6.7), between sources and mobilization row
draw_leak(8.0, 6.85,
          'No BMP can address legacy soil P\non policy-relevant timescales',
          width=3.5)

# === ARROWS DOWN from sources to mobilization ===
draw_arrow(2.0, 7.5, 2.0, 6.5)
draw_arrow(5.5, 7.5, 5.5, 6.5)

# === ROW 2: MOBILIZATION ===
draw_box(2.0, 5.3, 5.5, 1.2,
         'MOBILIZATION: Precipitation\n'
         'Thames P load: 80-670 t/yr (8x range)\n'
         '10-15% of flow days carry 60%+ of annual P load',
         C_PROCESS, fontsize=8, bold=True)

draw_leak(11.8, 5.9,
          'Precipitation controls all.\n8x noise vs BMP signal',
          width=3.2)

# === ARROWS DOWN (split into two pathways) ===
draw_arrow(3.5, 5.3, 2.5, 4.3)
draw_arrow(6.0, 5.3, 7.5, 4.3)

# === ROW 3: TRANSPORT PATHWAYS ===
# Surface runoff (left)
draw_box(0.5, 3.1, 3.5, 1.2,
         'SURFACE RUNOFF\nParticulate P (PP)\n70-90% of field loss\n25-50% bioavailable',
         C_PROCESS, fontsize=8, bold=True)

# Tile drainage (center)
draw_box(5.5, 3.1, 3.5, 1.2,
         'TILE DRAINAGE\nDissolved P (DRP)\n10-30% of field loss\n~100% bioavailable',
         C_PROCESS, fontsize=8, bold=True)

# Type A BMP (right)
draw_bmp_box(11.8, 3.8, 3.7, 1.2,
             'TYPE A BMP\nCover crop, No-till\n-30 to -60% PP\n$30/acre -- dormant at snowmelt',
             fontsize=7.8)

# Arrow: Type A reduces surface erosion/PP (label_dy raised to clear the
# TILE DRAINAGE box top at y=4.3 — larger than the default 0.18)
draw_arrow(11.8, 4.4, 4.0, 4.0, 'Reduces PP in runoff', C_BMP, label_dy=0.35)

# Leak: Type A can't intercept tile drainage
draw_leak(11.8, 3.0,
          'Type A CANNOT\nintercept tile DRP',
          width=2.6)
# Small warning arrow from leak toward tile-drainage box
ax.annotate('', xy=(9.1, 3.5), xytext=(10.8, 3.1),
            arrowprops=dict(arrowstyle='->', color=C_WARNING, lw=1.5,
                            linestyle='dashed'))

# === ARROWS DOWN from pathways to delivery ===
draw_arrow(2.25, 3.1, 4.0, 2.0)
draw_arrow(7.25, 3.1, 5.5, 2.0)

# === ROW 4: DELIVERY + LAKE ===
draw_box(3.0, 0.8, 4.5, 1.2,
         'DELIVERY TO RIVER\nDistance-dependent (mean 1.9 km)\n'
         'Fanshawe Reservoir retains 25% (2018) / 47% (2019)',
         C_PROCESS, fontsize=8, bold=True)

# "No spatial targeting" leak placed above the Lake Erie box, below the Type A leak
draw_leak(11.8, 2.45,
          'No spatial targeting\nin current UTRCA design',
          width=3.2)

# === ARROW TO LAKE ===
draw_arrow(7.5, 1.4, 9.8, 1.4)

# Lake Erie (moved slightly right to make room)
draw_box(10.0, 0.8, 4.5, 1.2,
         'LAKE ERIE\nBioavailable P drives HABs\nTarget: -40% (64 t/yr reduction)',
         C_BIOAVAIL, fontsize=8, bold=True)

# === LEGEND ===
legend_elements = [
    mpatches.Patch(facecolor=C_SOURCE, label='P sources', alpha=0.85),
    mpatches.Patch(facecolor=C_PROCESS, label='Transport processes', alpha=0.85),
    mpatches.Patch(facecolor=C_BMP, label='BMP intervention points', alpha=0.85),
    mpatches.Patch(facecolor='#FDF2E9', edgecolor=C_WARNING,
                   label='Structural limits (no BMP solution)'),
    mpatches.Patch(facecolor=C_BIOAVAIL, label='Ecological endpoint', alpha=0.85),
]
ax.legend(handles=legend_elements, loc='lower left', fontsize=8,
          framealpha=0.9, edgecolor=C_LOSS)

plt.tight_layout()
plt.savefig(str(_REPO / "results/figures/fig1_transport_chain.png"),
            dpi=300, bbox_inches='tight', facecolor='white')
plt.savefig(str(_REPO / "results/figures/fig1_transport_chain.pdf"),
            bbox_inches='tight', facecolor='white')
print("Saved: fig1_transport_chain.png + .pdf")
