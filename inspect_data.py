from pathlib import Path
import geopandas as gpd

# Locate the project folder
PROJECT_DIR = Path(__file__).resolve().parent

# Locate the downloaded GeoJSON
FILE_PATH = PROJECT_DIR / "data" / "raw" / "sjrwmd_stations.geojson"

# Read the spatial dataset
gdf = gpd.read_file(FILE_PATH)

print("\nSJRWMD DATA QUALITY INSPECTION")
print("--------------------------------")

# Dataset information
print("Total records:", len(gdf))
print("Coordinate system:", gdf.crs)
print("Geometry types:")
print(gdf.geometry.geom_type.value_counts())

# Inspect attributes
print("\nAVAILABLE FIELDS")
print("--------------------------------")

for column in gdf.columns:
    print(column)

# Missing values
print("\nMISSING VALUES BY FIELD")
print("--------------------------------")

missing = gdf.isna().sum().sort_values(ascending=False)

for field, count in missing.items():
    print(f"{field}: {count}")

# Geometry checks
print("\nGEOMETRY QUALITY")
print("--------------------------------")

print("Missing geometries:", gdf.geometry.isna().sum())
print("Empty geometries:", gdf.geometry.is_empty.sum())
print("Invalid geometries:", (~gdf.geometry.is_valid).sum())

print("\nInspection complete.")

print("\nSTATION IDENTIFIER QUALITY")
print("--------------------------------")

print("Missing station IDs:", gdf["STN_ID"].isna().sum())

duplicate_ids = gdf["STN_ID"].duplicated(keep=False)

print("Records with repeated station IDs:", duplicate_ids.sum())
print("Unique station IDs:", gdf["STN_ID"].nunique())

if duplicate_ids.any():
    print("\nSample repeated identifiers:")
    print(
        gdf.loc[duplicate_ids, ["OBJECTID", "STN_ID", "STN_NM"]]
        .head(20)
        .to_string(index=False)
    )
