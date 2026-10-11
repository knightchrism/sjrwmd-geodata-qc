import requests

# Public SJRWMD groundwater monitoring service
SERVICE_URL = (
    "https://services.arcgis.com/s8wtJX9suxFen6TA/ArcGIS/rest/services/"
    "Active_Groundwater_Monitoring_Network_Water_Level_Event_Type/"
    "FeatureServer/0"
)

# Request service information
response = requests.get(SERVICE_URL, params={"f": "json"}, timeout=30)

response.raise_for_status()

data = response.json()

# Check for an ArcGIS REST application-level error
if "error" in data:
    raise RuntimeError(data["error"])

print("\nSJRWMD FEATURE SERVICE INSPECTION")
print("--------------------------------")

print("Layer name:", data.get("name"))
print("Geometry type:", data.get("geometryType"))
print("Maximum records per request:", data.get("maxRecordCount"))

print("\nAVAILABLE FIELDS")
print("--------------------------------")

for field in data.get("fields", []):
    print(field["name"], "-", field.get("type"))

# Request the actual feature count
count_response = requests.get(
    SERVICE_URL + "/query",
    params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
    timeout=30,
)

count_response.raise_for_status()
count_data = count_response.json()

if "error" in count_data:
    raise RuntimeError(count_data["error"])

print("\nTOTAL FEATURES:", count_data.get("count"))

import json
from pathlib import Path

output_file = Path("data/raw/sjrwmd_service_metadata.json")

output_file.parent.mkdir(parents=True, exist_ok=True)

with open(output_file, "w", encoding="utf-8") as file:
    json.dump(data, file, indent=4)

print("\nMetadata saved to:", output_file)
