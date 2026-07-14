import pathlib
"""
03_build_field_agents.py
Use AAFC Annual Crop Inventory to create field-level agents.
1. Clip crop raster to Upper Thames boundary
2. Filter to agricultural crops only
3. Vectorize into field polygons
4. Overlay with soil attributes for P-risk
5. Save as agent-ready dataset
"""

import geopandas as gpd
import rasterio
from rasterio.mask import mask as rio_mask
from rasterio.features import shapes
import numpy as np
import pandas as pd
from shapely.geometry import shape
from pathlib import Path

_REPO = pathlib.Path(__file__).resolve().parents[2]

RAW = (_REPO / "data/raw")
PROCESSED = (_REPO / "data/processed")

# AAFC crop codes for agricultural crops (the ones we care about)
# Source: https://open.canada.ca/data/en/dataset/ba2645d5-4458-414d-b196-6303ac06c1c9
AG_CROP_CODES = {
    110: 'Soybean',      # may also be 122
    120: 'Corn',          # may also be 147
    122: 'Soybean',
    130: 'Barley',
    131: 'Barley',
    132: 'Barley',
    133: 'Barley',
    136: 'Canola',
    137: 'Canola',
    139: 'Mustard',
    140: 'Wheat',
    145: 'Managed Grassland',
    146: 'Alfalfa',
    147: 'Corn',
    148: 'Oats',
    153: 'Flaxseed',
    154: 'Rye',
    156: 'Buckwheat',
    157: 'Mixed Grains',
    158: 'Hay/Forages',
    160: 'Tobacco',
    162: 'Vegetables',
    167: 'Potatoes',
    174: 'Winter Wheat',
    175: 'Spring Wheat',
    176: 'Corn',
    177: 'Soybean',
    193: 'Beans',
    194: 'Peas',
    195: 'Lentils',
    196: 'Sugar Beet',
    197: 'Sunflower',
}

# Simplified crop categories for the model
def classify_crop(code):
    """Map AAFC code to simplified crop type."""
    name = AG_CROP_CODES.get(code, None)
    if name is None:
        return None  # Not an agricultural crop
    if name in ('Corn', 'Soybean', 'Wheat', 'Winter Wheat', 'Spring Wheat',
                'Barley', 'Mixed Grains', 'Rye', 'Oats', 'Buckwheat'):
        return 'Row Crop'  # High P application
    elif name in ('Managed Grassland', 'Alfalfa', 'Hay/Forages'):
        return 'Forage'    # Lower P application
    else:
        return 'Other Crop'


print("=" * 60)
print("BUILDING FIELD-LEVEL AGENTS FROM AAFC CROP INVENTORY")
print("=" * 60)

# 1. Load Upper Thames boundary
print("\n[1/5] Loading boundary...")
boundary = gpd.read_file(PROCESSED / "upper_thames_boundary.gpkg")

# 2. Clip crop raster to Upper Thames
print("\n[2/5] Clipping crop raster to Upper Thames...")
crop_path = RAW / "land_use" / "aci_2024_on" / "aci_2024_on_v2.tif"

with rasterio.open(crop_path) as src:
    crop_crs = src.crs
    print(f"  Crop raster CRS: {crop_crs}")

    # Reproject boundary to match raster CRS
    boundary_reproj = boundary.to_crs(crop_crs)

    # Clip raster
    clipped, transform = rio_mask(src, boundary_reproj.geometry, crop=True)
    clipped = clipped[0]  # First band

    profile = src.profile.copy()
    profile.update({
        'height': clipped.shape[0],
        'width': clipped.shape[1],
        'transform': transform
    })

print(f"  Clipped size: {clipped.shape}")
print(f"  Unique codes in Thames area: {len(np.unique(clipped))}")

# 3. Filter to agricultural pixels only
print("\n[3/5] Filtering to agricultural crops...")
ag_mask = np.isin(clipped, list(AG_CROP_CODES.keys()))
ag_pixels = np.sum(ag_mask)
total_pixels = np.sum(clipped > 0)
print(f"  Agricultural pixels: {ag_pixels:,} ({ag_pixels/max(total_pixels,1)*100:.1f}% of non-zero)")

# Zero out non-agricultural pixels
ag_raster = np.where(ag_mask, clipped, 0)

# 4. Vectorize into field polygons
print("\n[4/5] Vectorizing into field polygons...")
print("  (This may take a few minutes...)")

field_geometries = []
field_crops = []
field_codes = []

for geom, value in shapes(ag_raster.astype(np.int32), transform=transform):
    if value == 0:
        continue
    poly = shape(geom)
    area_ha = poly.area / 10000  # Depends on CRS units

    # Skip very small fields (< 2ha, likely noise)
    if area_ha < 2:
        continue

    field_geometries.append(poly)
    field_codes.append(int(value))
    field_crops.append(classify_crop(int(value)))

print(f"  Raw fields: {len(field_geometries)}")

# Create GeoDataFrame
fields = gpd.GeoDataFrame({
    'crop_code': field_codes,
    'crop_type': field_crops,
    'geometry': field_geometries
}, crs=crop_crs)

# Convert to UTM for area calculation
fields_utm = fields.to_crs("EPSG:32617")
fields_utm['area_ha'] = fields_utm.geometry.area / 10000
fields_utm['area_acres'] = fields_utm['area_ha'] * 2.471

# Filter by reasonable field size (2-500 ha)
fields_utm = fields_utm[(fields_utm['area_ha'] >= 2) & (fields_utm['area_ha'] <= 500)].copy()
fields_utm = fields_utm.reset_index(drop=True)

print(f"  Fields after size filter (2-500ha): {len(fields_utm)}")
print(f"  Total agricultural area: {fields_utm['area_ha'].sum():.0f} ha")
print(f"  Average field size: {fields_utm['area_ha'].mean():.1f} ha")
print(f"  Median field size: {fields_utm['area_ha'].median():.1f} ha")
print(f"\n  Crop type distribution:")
for ct, count in fields_utm['crop_type'].value_counts().items():
    area = fields_utm[fields_utm['crop_type']==ct]['area_ha'].sum()
    print(f"    {ct}: {count} fields, {area:.0f} ha")

# 5. Overlay with soil P-risk data
print("\n[5/5] Overlaying with soil P-risk data...")
soil = gpd.read_file(PROCESSED / "soil_p_risk_upper_thames.gpkg")
soil_utm = soil.to_crs("EPSG:32617")

# Spatial join: each field gets the soil attributes of its centroid
fields_utm['centroid_geom'] = fields_utm.geometry.centroid
centroid_gdf = gpd.GeoDataFrame(
    fields_utm[['crop_code', 'crop_type', 'area_ha', 'area_acres']],
    geometry=fields_utm['centroid_geom'],
    crs="EPSG:32617"
)

joined = gpd.sjoin(centroid_gdf, soil_utm[['p_risk', 'risk_level', 'drainage_score',
                                            'slope_pct', 'clay_score', 'dist_to_water',
                                            'geometry']],
                   how='left', predicate='within')

# Some centroids may fall outside soil polygons, fill with median
for col in ['p_risk', 'drainage_score', 'slope_pct', 'clay_score', 'dist_to_water']:
    median_val = joined[col].median()
    joined[col] = joined[col].fillna(median_val)

joined['risk_level'] = joined['risk_level'].fillna('Medium')

# Restore original field geometry
joined['geometry'] = fields_utm.geometry.values
joined = joined.drop(columns=['centroid_geom', 'index_right'], errors='ignore')

# Save
output_path = PROCESSED / "field_agents_upper_thames.gpkg"
joined.to_file(output_path, driver="GPKG")

print(f"\n  Saved: {output_path}")
print(f"  Total fields: {len(joined)}")
print(f"  Total area: {joined['area_ha'].sum():.0f} ha")
print(f"  Avg field size: {joined['area_ha'].mean():.1f} ha")

print(f"\n  P-risk by crop type:")
for ct in ['Row Crop', 'Forage', 'Other Crop']:
    subset = joined[joined['crop_type'] == ct]
    if len(subset) > 0:
        print(f"    {ct}: avg P-risk={subset['p_risk'].mean():.1f}, "
              f"n={len(subset)}, area={subset['area_ha'].sum():.0f}ha")

print(f"\n  Risk level distribution:")
for level in ['High', 'Medium', 'Low']:
    n = (joined['risk_level'] == level).sum()
    print(f"    {level}: {n} fields ({n/len(joined)*100:.0f}%)")

print("\n" + "=" * 60)
print("FIELD AGENT DATASET COMPLETE")
print("=" * 60)
print(f"\nNext: update environment.py to load field_agents_upper_thames.gpkg")
print(f"Then recalibrate and run Monte Carlo")
