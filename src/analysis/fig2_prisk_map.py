import pathlib
"""
Figure 2: P-risk choropleth map of Upper Thames watershed.
"""
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from pathlib import Path

_REPO = pathlib.Path(__file__).resolve().parents[2]
PROCESSED = (_REPO / "data/processed")
RAW = (_REPO / "data/raw")
FIGURES = (_REPO / "results/figures")

print("Loading data...")
fields = gpd.read_file(PROCESSED / "field_agents_upper_thames.gpkg")
boundary = gpd.read_file(PROCESSED / "upper_thames_boundary.gpkg")
rivers = gpd.read_file(RAW / "hydro_network" / "ohn_watercourse.geojson")

# Re-download rivers for correct bbox
import json, urllib.request, urllib.parse


boundary_4326 = boundary.to_crs("EPSG:4269")
b = boundary_4326.total_bounds  # xmin, ymin, xmax, ymax
bbox = json.dumps({"xmin": float(b[0])-0.05, "ymin": float(b[1])-0.05,
                   "xmax": float(b[2])+0.05, "ymax": float(b[3])+0.05,
                   "spatialReference": {"wkid": 4269}})
url = ("https://ws.lioservices.lrc.gov.on.ca/arcgis1071a/rest/services/"
       "LIO_OPEN_DATA/LIO_Open01/MapServer/26/query?" +
       urllib.parse.urlencode({"where": "1=1", "geometry": bbox,
        "geometryType": "esriGeometryEnvelope", "spatialRel": "esriSpatialRelIntersects",
        "outFields": "OGF_ID", "f": "geojson", "resultRecordCount": 5000}))

print("  Downloading rivers for Upper Thames bbox...")
with urllib.request.urlopen(url, timeout=120) as resp:
    rivers = gpd.read_file(resp)
print(f"  Got {len(rivers)} river segments")

# Reproject all to UTM 17N
fields = fields.to_crs("EPSG:32617")
boundary = boundary.to_crs("EPSG:32617")
rivers = rivers.to_crs("EPSG:32617")

# Clip rivers to watershed boundary (with a small 500 m buffer so edge
# segments are not truncated). Eliminates the out-of-watershed "scribble"
# artifact from the bbox-expanded OHN download.
boundary_buffered = boundary.copy()
boundary_buffered['geometry'] = boundary_buffered.geometry.buffer(500)
rivers = gpd.clip(rivers, boundary_buffered)

print(f"Fields: {len(fields)}, Rivers (clipped): {len(rivers)}")

# Color map
risk_colors = {'High': '#E74C3C', 'Medium': '#F1C40F', 'Low': '#27AE60'}
fields['color'] = fields['risk_level'].map(risk_colors)

fig, ax = plt.subplots(1, 1, figsize=(12, 10))

# Watershed boundary
boundary.plot(ax=ax, facecolor='none', edgecolor='black', linewidth=2, zorder=3)

# Fields by risk level (plot in order so High is on top)
for level, color in [('Low', '#27AE60'), ('Medium', '#F1C40F'), ('High', '#E74C3C')]:
    subset = fields[fields['risk_level'] == level]
    subset.plot(ax=ax, color=color, alpha=0.7, edgecolor='none', zorder=1)

# Rivers
rivers.plot(ax=ax, color='#3498DB', linewidth=0.5, alpha=0.6, zorder=2)

# Legend
legend_elements = [
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#E74C3C',
           markersize=12, label=f'High risk ({(fields.risk_level=="High").sum()} fields, 25% of area)'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#F1C40F',
           markersize=12, label=f'Medium risk ({(fields.risk_level=="Medium").sum()} fields, 50% of area)'),
    Line2D([0], [0], marker='s', color='w', markerfacecolor='#27AE60',
           markersize=12, label=f'Low risk ({(fields.risk_level=="Low").sum()} fields, 26% of area)'),
    Line2D([0], [0], color='#3498DB', linewidth=1.5, label='Watercourses'),
    Line2D([0], [0], color='black', linewidth=2, label='Watershed boundary'),
]
ax.legend(handles=legend_elements, loc='lower right', fontsize=10,
          framealpha=0.9, edgecolor='gray')

ax.set_title('Phosphorus Loss Risk Classification\nUpper Thames River Watershed (8,949 agricultural fields)',
             fontsize=14, fontweight='bold')
ax.set_xlabel('Easting (m, UTM 17N)')
ax.set_ylabel('Northing (m, UTM 17N)')

# Scale bar (approximate)
x0, y0 = ax.get_xlim()[0] + 3000, ax.get_ylim()[0] + 3000
ax.plot([x0, x0 + 10000], [y0, y0], 'k-', linewidth=3)
ax.text(x0 + 5000, y0 + 1500, '10 km', ha='center', fontsize=10)

plt.tight_layout()
plt.savefig(FIGURES / 'fig2_prisk_map.png', dpi=300, bbox_inches='tight')
print("Saved fig2_prisk_map.png")
