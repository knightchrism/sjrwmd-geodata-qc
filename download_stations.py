import json
from pathlib import Path

import requests

# 1. Project folders
PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = PROJECT_DIR / "data" / "raw" / "sjrwmd_stations.geojson"

# 2. ArcGIS REST feature layer
SERVICE_URL = (
    "https://services.arcgis.com/s8wtJX9suxFen6TA/ArcGIS/rest/services/"
    "Active_Groundwater_Monitoring_Network_Water_Level_Event_Type/"
    "FeatureServer/0/query"
)

# 3. Query parameters
params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "true",
    "outSR": 4326,
    "f": "geojson",
}

print("Downloading SJRWMD monitoring stations...")

# 4. Request data
response = requests.get(SERVICE_URL, params=params, timeout=60)

response.raise_for_status()
data = response.json()

if "error" in data:
    raise RuntimeError(data["error"])

if data.get("type") != "FeatureCollection":
    raise RuntimeError("Unexpected GeoJSON response.")

# 5. Verify downloaded records
features = data.get("features", [])

print("Features downloaded:", len(features))

if len(features) != 850:
    raise RuntimeError(
        f"Expected 850 features, received {len(features)}. "
        "Check service limits or source updates."
    )

# 6. Save source records
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=2)

print("Saved:", OUTPUT_FILE)
print("Download complete.")
