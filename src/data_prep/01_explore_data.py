import pathlib
"""
01_explore_data.py
First look at all downloaded datasets. Load, check CRS, fields, and basic stats.
Clip everything to Upper Thames watershed boundary.
Output: summary of each dataset + initial maps.
"""

import geopandas as gpd
import json
import os
import numpy as np
from pathlib import Path

_REPO = pathlib.Path(__file__).resolve().parents[2]

# Paths
RAW = (_REPO / "data/raw")
PROCESSED = (_REPO / "data/processed")
FIGURES = (_REPO / "results/figures")
PROCESSED.mkdir(exist_ok=True)
FIGURES.mkdir(exist_ok=True)

TARGET_CRS = "EPSG:32617"  # UTM Zone 17N

print("=" * 60)
print("DATA EXPLORATION - BMP Thesis")
print("=" * 60)

# ============================================================
# 1. WATERSHED BOUNDARY (the most important - defines study area)
# ============================================================
print("\n[1] WATERSHED BOUNDARIES")
print("-" * 40)

wb = gpd.read_file(RAW / "watershed_boundaries" / "owb_tertiary.geojson")
print(f"CRS: {wb.crs}")
print(f"Total features: {len(wb)}")
print(f"Fields: {list(wb.columns)}")
print()

# Extract Upper Thames
upper_thames = wb[wb["WATERSHED_NAME"] == "Upper Thames River"].copy()
lower_thames = wb[wb["WATERSHED_NAME"] == "Lower Thames River"].copy()
print(f"Upper Thames: {upper_thames.iloc[0]['AREA_HECTARE']:.0f} ha")
print(f"Lower Thames: {lower_thames.iloc[0]['AREA_HECTARE']:.0f} ha")

# Reproject to UTM 17N
upper_thames_utm = upper_thames.to_crs(TARGET_CRS)
print(f"Upper Thames UTM bounds: {upper_thames_utm.total_bounds}")
print(f"Upper Thames UTM area: {upper_thames_utm.geometry.area.iloc[0] / 1e6:.0f} km2")

# Save Upper Thames boundary for clipping
upper_thames_utm.to_file(PROCESSED / "upper_thames_boundary.gpkg", driver="GPKG")
print(f"Saved: upper_thames_boundary.gpkg")

# ============================================================
# 2. SOIL SURVEY
# ============================================================
print("\n[2] SOIL SURVEY COMPLEX")
print("-" * 40)

soil_path = RAW / "soil_survey" / "soilomaf.shp"
if soil_path.exists():
    print(f"File size: {soil_path.stat().st_size / 1e6:.0f} MB")
    # Read only metadata first (don't load all geometry yet)
    soil_sample = gpd.read_file(soil_path, rows=10)
    print(f"CRS: {soil_sample.crs}")
    print(f"Fields ({len(soil_sample.columns)}): {list(soil_sample.columns)}")
    print(f"Sample values:")
    for col in soil_sample.columns:
        if col != 'geometry':
            vals = soil_sample[col].dropna().unique()[:5]
            print(f"  {col}: {list(vals)}")
else:
    print("NOT FOUND - check file path")

# ============================================================
# 3. OHN WATERCOURSE
# ============================================================
print("\n[3] OHN WATERCOURSE")
print("-" * 40)

ohn_path = RAW / "hydro_network" / "ohn_watercourse.geojson"
if ohn_path.exists():
    ohn = gpd.read_file(ohn_path)
    print(f"CRS: {ohn.crs}")
    print(f"Features: {len(ohn)}")
    print(f"Fields: {list(ohn.columns)}")
    print(f"Watercourse types: {ohn['WATERCOURSE_TYPE'].value_counts().to_dict()}")
    print(f"Permanency: {ohn['PERMANENCY'].value_counts().to_dict()}")
else:
    print("NOT FOUND")

# ============================================================
# 4. TILE DRAINAGE
# ============================================================
print("\n[4] TILE DRAINAGE AREA")
print("-" * 40)

td_path = RAW / "hydro_network" / "tile_drainage.geojson"
if td_path.exists():
    td = gpd.read_file(td_path)
    print(f"CRS: {td.crs}")
    print(f"Features: {len(td)}")
    print(f"Fields: {list(td.columns)}")
    # Show sample
    for col in td.columns:
        if col != 'geometry':
            vals = td[col].dropna().unique()[:5]
            print(f"  {col}: {list(vals)}")
else:
    print("NOT FOUND")

# ============================================================
# 5. DEM (SRTM)
# ============================================================
print("\n[5] DEM (SRTM)")
print("-" * 40)

dem_dir = RAW / "dem"
dem_files = list(dem_dir.glob("*.hgt.gz"))
print(f"DEM tiles: {len(dem_files)}")
for f in dem_files:
    print(f"  {f.name}: {f.stat().st_size / 1e6:.1f} MB")

# Try to read one tile with rasterio
try:
    import rasterio
    # Need to decompress first
    import gzip
    test_tile = dem_files[2]  # N43W081 should cover Thames
    with gzip.open(test_tile, 'rb') as gz:
        hgt_path = dem_dir / test_tile.stem
        with open(hgt_path, 'wb') as out:
            out.write(gz.read())

    with rasterio.open(hgt_path) as src:
        print(f"  Test tile ({test_tile.name}):")
        print(f"    CRS: {src.crs}")
        print(f"    Size: {src.width}x{src.height}")
        print(f"    Bounds: {src.bounds}")
        print(f"    Resolution: {src.res}")
        data = src.read(1)
        print(f"    Elevation range: {data.min()}-{data.max()} m")

    # Clean up
    os.remove(hgt_path)
except Exception as e:
    print(f"  Could not read DEM: {e}")

# ============================================================
# 6. CONSTRUCTED DRAIN
# ============================================================
print("\n[6] CONSTRUCTED DRAIN")
print("-" * 40)

cd_path = RAW / "hydro_network" / "constructed_drain.geojson"
if cd_path.exists():
    cd = gpd.read_file(cd_path)
    print(f"Features: {len(cd)}")
    print(f"Fields: {list(cd.columns)}")
else:
    print("NOT FOUND")

# ============================================================
# SUMMARY
# ============================================================
print("\n" + "=" * 60)
print("DATA INVENTORY SUMMARY")
print("=" * 60)

datasets = {
    "Watershed Boundary": "[OK]" if (PROCESSED / "upper_thames_boundary.gpkg").exists() else "[MISSING]",
    "Soil Survey": "[OK]" if soil_path.exists() else "[MISSING]",
    "OHN Watercourse": "[OK]" if ohn_path.exists() else "[MISSING]",
    "Tile Drainage": "[OK]" if td_path.exists() else "[MISSING]",
    "Constructed Drain": "[OK]" if cd_path.exists() else "[MISSING]",
    "DEM (SRTM)": "[OK]" if len(dem_files) == 4 else "[MISSING]",
    "OMAFRA Crop Budgets": "[OK]" if (RAW / "omafra_field_crop_budgets_2025.pdf").exists() else "[MISSING]",
    "Farm Parcels": "[PENDING] pending (email sent)",
}

for name, status in datasets.items():
    print(f"  {status} {name}")

print("\nNext step: Clip Soil Survey to Upper Thames boundary → compute P-risk score")
