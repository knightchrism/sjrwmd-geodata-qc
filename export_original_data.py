from pathlib import Path
import geopandas as gpd

# Locate our project
PROJECT_DIR = Path(__file__).resolve().parent

# Original downloaded GeoJSON
SOURCE_FILE = PROJECT_DIR / "data" / "raw" / "sjrwmd_stations.geojson"

# Export destination
OUTPUT_FILE = PROJECT_DIR / "reports" / "sjrwmd_original_attributes.csv"

# Read original records
gdf = gpd.read_file(SOURCE_FILE)

# Preserve every original attribute column
# Geometry is stored separately in the GeoJSON
attributes = gdf.drop(columns="geometry")

# Export to CSV
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

attributes.to_csv(OUTPUT_FILE, index=False)

print("Original attributes exported!")
print("Records:", len(attributes))
print("Fields:", len(attributes.columns))
print("Saved to:", OUTPUT_FILE)

print("\nUTM Coordinate Completeness:")
print("Missing UTM_X:", attributes["UTM_X"].isna().sum())
print("Missing UTM_Y:", attributes["UTM_Y"].isna().sum())
