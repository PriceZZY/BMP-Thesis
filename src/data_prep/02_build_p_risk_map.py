"""
02_build_p_risk_map.py
1. Load Soil Survey shapefile + attribute table
2. Join on OBJECT_ID / FMF_OBJECT_ID
3. Clip to Upper Thames watershed
4. Compute slope from DEM
5. Compute distance to nearest waterway
6. Calculate P-risk score
7. Save final dataset
"""

import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.mask import mask as rio_mask
from shapely.geometry import Point
from pathlib import Path
import json
import gzip
import os

RAW = Path("D:/Claude/BMP-Thesis/data/raw")
PROCESSED = Path("D:/Claude/BMP-Thesis/data/processed")
TARGET_CRS = "EPSG:32617"

print("=" * 60)
print("BUILDING P-RISK MAP")
print("=" * 60)

# ============================================================
# 1. Load Upper Thames boundary
# ============================================================
print("\n[1/6] Loading Upper Thames boundary...")
boundary = gpd.read_file(PROCESSED / "upper_thames_boundary.gpkg")
boundary_4269 = boundary.to_crs("EPSG:4269")  # Match soil survey CRS
boundary_4326 = boundary.to_crs("EPSG:4326")  # Match watercourse CRS
print(f"  Boundary loaded: {boundary.crs}")

# ============================================================
# 2. Load and join Soil Survey
# ============================================================
print("\n[2/6] Loading Soil Survey + attribute table...")

# Load attribute table
tbl_path = RAW / "soil_survey" / "soil_survey_complex_ft.tbl"
soil_attrs = pd.read_csv(tbl_path, dtype=str, low_memory=False)
print(f"  Attribute table: {len(soil_attrs)} rows, {len(soil_attrs.columns)} columns")
print(f"  Key fields: DRAINAGE1={soil_attrs['DRAINAGE1'].nunique()} unique, "
      f"ATEXTURE1={soil_attrs['ATEXTURE1'].nunique()} unique")

# Load soil shapefile - clip to Thames bbox first to reduce memory
print("  Loading soil shapefile (clipping to Thames area)...")
thames_bbox = boundary_4269.total_bounds  # [xmin, ymin, xmax, ymax]
soil = gpd.read_file(
    RAW / "soil_survey" / "soilomaf.shp",
    bbox=tuple(thames_bbox)
)
print(f"  Soil polygons in Thames area: {len(soil)}")

# Join attributes
soil_attrs['FMF_OBJECT_ID'] = soil_attrs['FMF_OBJECT_ID'].astype(int)
soil = soil.merge(soil_attrs, left_on='OBJECT_ID', right_on='FMF_OBJECT_ID', how='left')
print(f"  After join: {len(soil)} rows")

# Clip to Upper Thames boundary
print("  Clipping to Upper Thames boundary...")
soil_utm = soil.to_crs(TARGET_CRS)
boundary_utm = boundary.to_crs(TARGET_CRS)
soil_thames = gpd.clip(soil_utm, boundary_utm)
print(f"  Soil polygons in Upper Thames: {len(soil_thames)}")

# ============================================================
# 3. Parse drainage class score
# ============================================================
print("\n[3/6] Computing drainage score...")

# Drainage codes to numeric score (higher = worse drainage = higher P risk)
drainage_map = {
    'R': 1,    # Rapid
    'W': 2,    # Well
    'MW': 3,   # Moderately Well
    'I': 4,    # Imperfect
    'P': 5,    # Poor
    'VP': 6,   # Very Poor
    'WA': np.nan,  # Water
    'VA': np.nan,  # Variable / Not mapped
    '': np.nan
}

soil_thames['drainage_score'] = soil_thames['DRAINAGE1'].map(drainage_map)
print(f"  Drainage score distribution:")
print(f"  {soil_thames['drainage_score'].value_counts().sort_index().to_dict()}")

# ============================================================
# 4. Parse slope class
# ============================================================
print("\n[4/6] Computing slope score...")

# Slope class to approximate percentage
slope_map = {
    'A': 0.5,   # 0-0.5%
    'B': 1.0,   # 0-2%
    'C': 3.5,   # 2-5%
    'c': 3.5,   # 2-5% (lowercase variant)
    'D': 7.0,   # 5-9%
    'd': 7.0,
    'E': 12.5,  # 9-15%
    'e': 12.5,
    'F': 22.5,  # 15-30%
    'f': 22.5,
    'G': 45.0,  # 30-60%
    'g': 45.0,
}

soil_thames['slope_pct'] = soil_thames['CLASS1'].map(slope_map)
# Fill missing with median
median_slope = soil_thames['slope_pct'].median()
soil_thames['slope_pct'] = soil_thames['slope_pct'].fillna(median_slope)
print(f"  Slope distribution: mean={soil_thames['slope_pct'].mean():.1f}%, "
      f"median={soil_thames['slope_pct'].median():.1f}%")

# ============================================================
# 5. Parse texture (clay indicator)
# ============================================================
print("\n[5/6] Computing clay score...")

# Texture codes that indicate high clay content
clay_textures = {'C', 'HC', 'SIC', 'SICL', 'CL', 'SCL'}
medium_textures = {'L', 'SIL', 'FSL', 'VFSL', 'SI'}
sandy_textures = {'S', 'LS', 'SL', 'LFS', 'FS', 'VFS', 'CS', 'GS'}

def texture_to_clay_score(tex):
    if pd.isna(tex) or tex.strip() == '' or tex.strip('_') == '':
        return np.nan
    tex = tex.strip().strip('_').upper()
    if tex in clay_textures:
        return 3  # High clay
    elif tex in medium_textures:
        return 2  # Medium
    elif tex in sandy_textures:
        return 1  # Sandy (low clay)
    else:
        return 2  # Default to medium

soil_thames['clay_score'] = soil_thames['ATEXTURE1'].apply(texture_to_clay_score)
print(f"  Clay score distribution: {soil_thames['clay_score'].value_counts().sort_index().to_dict()}")

# ============================================================
# 6. Compute distance to nearest waterway
# ============================================================
print("\n[6/6] Computing distance to nearest waterway...")

# Load watercourse
ohn = gpd.read_file(RAW / "hydro_network" / "ohn_watercourse.geojson")
ohn_utm = ohn.to_crs(TARGET_CRS)

# Merge all waterways into one multi-line geometry for fast distance calc
all_water = ohn_utm.geometry.unary_union

# Compute centroid of each soil polygon, then distance to nearest waterway
soil_thames['centroid'] = soil_thames.geometry.centroid
soil_thames['dist_to_water'] = soil_thames['centroid'].apply(
    lambda pt: pt.distance(all_water)
)
print(f"  Distance range: {soil_thames['dist_to_water'].min():.0f} - "
      f"{soil_thames['dist_to_water'].max():.0f} m")
print(f"  Mean distance: {soil_thames['dist_to_water'].mean():.0f} m")

# ============================================================
# 7. Compute P-risk score
# ============================================================
print("\n" + "=" * 60)
print("COMPUTING P-RISK SCORE")
print("=" * 60)

# Normalize each component to 0-1
soil_thames['drainage_norm'] = soil_thames['drainage_score'].fillna(3) / 6.0
soil_thames['slope_norm'] = np.clip(soil_thames['slope_pct'] / 15.0, 0, 1)
soil_thames['proximity_norm'] = np.clip(1.0 - (soil_thames['dist_to_water'] / 5000.0), 0, 1)
soil_thames['clay_norm'] = soil_thames['clay_score'].fillna(2) / 3.0

# Weighted P-risk score (from Section 16 of PROJECT_PLAN.md)
W_DRAINAGE = 0.30
W_SLOPE = 0.25
W_PROXIMITY = 0.25
W_CLAY = 0.20

soil_thames['p_risk_raw'] = (
    W_DRAINAGE * soil_thames['drainage_norm'] +
    W_SLOPE * soil_thames['slope_norm'] +
    W_PROXIMITY * soil_thames['proximity_norm'] +
    W_CLAY * soil_thames['clay_norm']
)

# Scale to 0-100
soil_thames['p_risk'] = (soil_thames['p_risk_raw'] * 100).round(1)

print(f"\nP-risk score statistics:")
print(f"  Mean: {soil_thames['p_risk'].mean():.1f}")
print(f"  Median: {soil_thames['p_risk'].median():.1f}")
print(f"  Std: {soil_thames['p_risk'].std():.1f}")
print(f"  Min: {soil_thames['p_risk'].min():.1f}")
print(f"  Max: {soil_thames['p_risk'].max():.1f}")

# Classify using simple terciles (Jenks requires additional library)
terciles = soil_thames['p_risk'].quantile([0.33, 0.67]).values
soil_thames['risk_level'] = pd.cut(
    soil_thames['p_risk'],
    bins=[-1, terciles[0], terciles[1], 100],
    labels=['Low', 'Medium', 'High']
)

print(f"\nRisk classification (tercile-based):")
print(f"  Thresholds: Low < {terciles[0]:.1f} < Medium < {terciles[1]:.1f} < High")
risk_counts = soil_thames['risk_level'].value_counts()
for level in ['Low', 'Medium', 'High']:
    if level in risk_counts.index:
        count = risk_counts[level]
        pct = count / len(soil_thames) * 100
        print(f"  {level}: {count} polygons ({pct:.0f}%)")

# ============================================================
# 8. Save results
# ============================================================
print("\n" + "=" * 60)
print("SAVING RESULTS")
print("=" * 60)

# Drop centroid column (not serializable to file)
output = soil_thames.drop(columns=['centroid'])

# Select key columns only to keep file manageable
key_cols = [
    'OBJECT_ID', 'MAPUNIT_x', 'SOIL_NAME1', 'DRAINAGE1', 'ATEXTURE1',
    'CLASS1', 'CLI1', 'SLOPE1',
    'drainage_score', 'slope_pct', 'clay_score', 'dist_to_water',
    'drainage_norm', 'slope_norm', 'proximity_norm', 'clay_norm',
    'p_risk_raw', 'p_risk', 'risk_level',
    'geometry'
]

# Only keep columns that exist
existing_cols = [c for c in key_cols if c in output.columns]
output = output[existing_cols]

output.to_file(PROCESSED / "soil_p_risk_upper_thames.gpkg", driver="GPKG")
print(f"  Saved: soil_p_risk_upper_thames.gpkg ({len(output)} polygons)")

# Also save a summary CSV
summary = output.drop(columns=['geometry']).describe()
summary.to_csv(PROCESSED / "p_risk_summary_stats.csv")
print(f"  Saved: p_risk_summary_stats.csv")

print("\n" + "=" * 60)
print("P-RISK MAP COMPLETE")
print("=" * 60)
print(f"\nTotal soil polygons in Upper Thames: {len(output)}")
print(f"Each polygon has a P-risk score (0-100) and risk level (Low/Medium/High)")
print(f"\nNext step: overlay with farm parcels (when available) or use soil polygons as agent units")
