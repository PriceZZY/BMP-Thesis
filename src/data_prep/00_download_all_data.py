import pathlib
"""
Download all required GIS data for the BMP Thesis project.
Uses ArcGIS REST API to query and download data for the Thames River watershed area.
"""

import json
import os
import urllib.request
import urllib.parse
import time

_REPO = pathlib.Path(__file__).resolve().parents[2]

# Project paths
RAW_DIR = str(_REPO / "data/raw")

# Thames River watershed approximate bounding box (NAD83 / EPSG:4269)
THAMES_BBOX = {
    "xmin": -81.9,
    "ymin": 42.5,
    "xmax": -80.5,
    "ymax": 43.6,
    "spatialReference": {"wkid": 4269}
}

# LIO Open Data MapServer base URL
LIO_BASE = "https://ws.lioservices.lrc.gov.on.ca/arcgis1071a/rest/services/LIO_OPEN_DATA/LIO_Open01/MapServer"

# Layers we need from LIO
LIO_LAYERS = {
    "ohn_watercourse": {"id": 26, "name": "OHN Watercourse"},
    "tile_drainage": {"id": 11, "name": "Tile Drainage Area"},
    "constructed_drain": {"id": 7, "name": "Constructed Drain"},
}

def download_lio_layer(layer_key, layer_info, bbox, output_dir, max_records=2000):
    """Download a LIO layer using spatial query with pagination."""
    layer_id = layer_info["id"]
    layer_name = layer_info["name"]
    out_file = os.path.join(output_dir, f"{layer_key}.geojson")

    if os.path.exists(out_file):
        print(f"  [SKIP] {layer_name} already downloaded")
        return

    print(f"  [START] Downloading {layer_name} (layer {layer_id})...")

    all_features = []
    offset = 0

    while True:
        params = {
            "where": "1=1",
            "geometry": json.dumps(bbox),
            "geometryType": "esriGeometryEnvelope",
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "*",
            "f": "geojson",
            "resultRecordCount": max_records,
            "resultOffset": offset,
        }

        url = f"{LIO_BASE}/{layer_id}/query?" + urllib.parse.urlencode(params)

        try:
            with urllib.request.urlopen(url, timeout=120) as response:
                data = json.loads(response.read().decode())
        except Exception as e:
            print(f"  [ERROR] Failed at offset {offset}: {e}")
            break

        features = data.get("features", [])
        if not features:
            break

        all_features.extend(features)
        print(f"    ... got {len(features)} features (total: {len(all_features)})")

        # Check if there are more records
        if not data.get("exceededTransferLimit", False) and not data.get("properties", {}).get("exceededTransferLimit", False):
            break

        offset += max_records
        time.sleep(0.5)  # Be polite to the server

    # Save as GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    with open(out_file, "w") as f:
        json.dump(geojson, f)

    print(f"  [DONE] {layer_name}: {len(all_features)} features saved to {out_file}")


def download_watershed_boundaries(output_dir):
    """Download Ontario Watershed Boundaries from the OWB service."""
    out_file = os.path.join(output_dir, "watershed_boundaries.geojson")

    if os.path.exists(out_file):
        print("  [SKIP] Watershed boundaries already downloaded")
        return

    print("  [START] Downloading Ontario Watershed Boundaries...")

    # OWB is on a different service endpoint
    # Try the GeoHub feature service
    owb_url = "https://ws.lioservices.lrc.gov.on.ca/arcgis1071a/rest/services/LIO_OPEN_DATA/LIO_Open02/MapServer"

    # First, find the watershed layer
    try:
        with urllib.request.urlopen(f"{owb_url}?f=json", timeout=30) as response:
            service_info = json.loads(response.read().decode())
            for layer in service_info.get("layers", []):
                name = layer.get("name", "").lower()
                if "watershed" in name:
                    print(f"    Found: {layer['name']} (ID: {layer['id']})")
    except Exception as e:
        print(f"  [INFO] LIO_Open02 check: {e}")

    # Try direct GeoHub feature service for OWB
    owb_urls_to_try = [
        "https://ws.lioservices.lrc.gov.on.ca/arcgis1071a/rest/services/LIO_OPEN_DATA/LIO_Open02/MapServer",
        "https://ws.lioservices.lrc.gov.on.ca/arcgis1071a/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer",
    ]

    for base_url in owb_urls_to_try:
        try:
            with urllib.request.urlopen(f"{base_url}?f=json", timeout=30) as response:
                data = json.loads(response.read().decode())
                for layer in data.get("layers", []):
                    if "watershed" in layer.get("name", "").lower():
                        print(f"    Found watershed layer: {layer['name']} at {base_url}/{layer['id']}")
        except:
            continue

    print("  [NOTE] If OWB not found via API, download manually from GeoHub or use Conservation Authority boundaries")


def download_omafra_crop_budgets(output_dir):
    """Download OMAFRA Field Crop Budgets PDF."""
    out_file = os.path.join(output_dir, "omafra_field_crop_budgets_2025.pdf")

    if os.path.exists(out_file):
        print(f"  [SKIP] OMAFRA crop budgets already downloaded")
        return

    url = "https://www.ontario.ca/files/2025-01/omafa-field-crop-budgets-pub-60-en-2025-01-14.pdf"
    print(f"  [START] Downloading OMAFRA Field Crop Budgets...")

    try:
        urllib.request.urlretrieve(url, out_file)
        size_mb = os.path.getsize(out_file) / 1024 / 1024
        print(f"  [DONE] Saved ({size_mb:.1f} MB)")
    except Exception as e:
        print(f"  [ERROR] {e}")


if __name__ == "__main__":
    print("=" * 60)
    print("BMP Thesis Data Download Script")
    print("=" * 60)

    # Create directories
    for subdir in ["hydro_network", "watershed_boundaries", "land_use"]:
        os.makedirs(os.path.join(RAW_DIR, subdir), exist_ok=True)

    # 1. Download LIO layers (OHN Watercourse, Tile Drainage)
    print("\n[1/3] LIO Open Data layers (Thames River area):")
    for key, info in LIO_LAYERS.items():
        download_lio_layer(key, info, THAMES_BBOX,
                          os.path.join(RAW_DIR, "hydro_network"))

    # 2. Download watershed boundaries
    print("\n[2/3] Watershed Boundaries:")
    download_watershed_boundaries(os.path.join(RAW_DIR, "watershed_boundaries"))

    # 3. Download OMAFRA crop budgets
    print("\n[3/3] OMAFRA Field Crop Budgets:")
    download_omafra_crop_budgets(RAW_DIR)

    print("\n" + "=" * 60)
    print("Download complete! Check output for any errors.")
    print("=" * 60)
    print("\nManual downloads still needed:")
    print("  - DEM: Search GeoHub for 'Provincial DEM' or use SRTM from USGS")
    print("  - Parcel data: Email librarygeo@library.uwaterloo.ca")
    print("  - UTRCA subwatershed boundaries: Check thamesriver-camaps.hub.arcgis.com")
