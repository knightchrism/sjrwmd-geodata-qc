from pathlib import Path
from datetime import datetime, timezone
import json
import math

import pandas as pd
import geopandas as gpd


# ==================================================
# 1. FILE PATHS
# ==================================================

PROJECT_DIR = Path(__file__).resolve().parent

SOURCE_FILE = PROJECT_DIR / "data" / "raw" / "sjrwmd_stations.geojson"

RULES_FILE = PROJECT_DIR / "config" / "qc_rules.json"

REPORTS_DIR = PROJECT_DIR / "reports"
WEB_DIR = PROJECT_DIR / "docs" / "data"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)


# ==================================================
# 2. READ DATA AND CONFIGURATION
# ==================================================

print("Loading monitoring stations...")

gdf = gpd.read_file(SOURCE_FILE)

with open(RULES_FILE, encoding="utf-8") as file:
    config = json.load(file)

rules = config["rules"]

print("Stations:", len(gdf))
print("Rules:", len(rules))


# ==================================================
# 3. HELPERS
# ==================================================


def missing(series):
    """Find null values and blank strings."""
    return series.isna() | series.astype("string").str.strip().eq("").fillna(False)


def safe_value(value):
    """Convert pandas values into JSON-compatible values."""
    if value is None:
        return None

    if isinstance(value, pd.Timestamp):
        return value.isoformat() if pd.notna(value) else None

    if isinstance(value, (list, dict, tuple)):
        return str(value)

    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass

    if hasattr(value, "item"):
        value = value.item()

    if isinstance(value, float) and not math.isfinite(value):
        return None

    return value


def fields_for_rule(rule):
    if "fields" in rule:
        return rule["fields"]
    return [rule["field"]]


def validate_rule(rule):
    supported = {
        "required",
        "missing",
        "unique",
        "geometry_present",
        "geometry_valid",
        "missing_any",
    }

    if rule["check"] not in supported:
        raise ValueError(f"Unsupported check: {rule['check']}")

    for field in fields_for_rule(rule):
        if field not in gdf.columns:
            raise ValueError(f"Rule {rule['id']} references missing field {field}")


def evaluate_rule(rule):
    check = rule["check"]
    fields = fields_for_rule(rule)

    if check in ("required", "missing"):
        return missing(gdf[fields[0]])

    if check == "unique":
        series = gdf[fields[0]]
        return ~missing(series) & series.duplicated(keep=False)

    if check == "geometry_present":
        return gdf.geometry.isna() | gdf.geometry.is_empty

    if check == "geometry_valid":
        return gdf.geometry.notna() & ~gdf.geometry.is_empty & ~gdf.geometry.is_valid

    if check == "missing_any":
        result = pd.Series(False, index=gdf.index)

        for field in fields:
            result = result | missing(gdf[field])

        return result

    raise ValueError(f"Unsupported check: {check}")


# ==================================================
# 4. RUN QC
# ==================================================

issues = []
rule_results = []

for rule in rules:
    validate_rule(rule)

    failed = evaluate_rule(rule).fillna(False)

    flagged_count = int(failed.sum())

    rule_results.append(
        {
            "rule_id": rule["id"],
            "rule_name": rule["name"],
            "severity": rule["severity"],
            "basis": rule.get("basis"),
            "interpretation": rule.get("interpretation"),
            "failed_records": flagged_count,
        }
    )

    print(rule["id"], rule["name"], "->", flagged_count)

    fields = fields_for_rule(rule)

    for _, row in gdf.loc[failed].iterrows():
        geometry = row.geometry

        longitude = None
        latitude = None

        if (
            geometry is not None
            and not geometry.is_empty
            and geometry.geom_type == "Point"
        ):
            longitude = safe_value(geometry.x)
            latitude = safe_value(geometry.y)

        original_values = {
            field: safe_value(row.get(field)) for field in fields if field != "geometry"
        }

        missing_fields = [
            field
            for field in fields
            if field != "geometry"
            and bool(missing(pd.Series([row.get(field)])).iloc[0])
        ]

        issues.append(
            {
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "basis": rule.get("basis", ""),
                "interpretation": rule.get("interpretation", ""),
                "objectid": safe_value(row.get("OBJECTID")),
                "station_id": safe_value(row.get("STN_ID")),
                "station_name": safe_value(row.get("STN_NM")),
                "county": safe_value(row.get("COUNTY")),
                "latitude": latitude,
                "longitude": longitude,
                "utm_x": safe_value(row.get("UTM_X")),
                "utm_y": safe_value(row.get("UTM_Y")),
                "missing_fields": ", ".join(missing_fields),
                "original_values": json.dumps(original_values),
                "review_status": "Needs review",
            }
        )


# ==================================================
# 5. SAVE CSV
# ==================================================

issue_columns = [
    "rule_id",
    "rule_name",
    "severity",
    "basis",
    "interpretation",
    "objectid",
    "station_id",
    "station_name",
    "county",
    "latitude",
    "longitude",
    "utm_x",
    "utm_y",
    "missing_fields",
    "original_values",
    "review_status",
]

issues_df = pd.DataFrame(issues, columns=issue_columns)

csv_file = REPORTS_DIR / "sjrwmd_qc_issues.csv"

issues_df.to_csv(csv_file, index=False, encoding="utf-8-sig")


# ==================================================
# 6. QC SUMMARY
# ==================================================

unique_flagged = issues_df["objectid"].dropna().nunique() if not issues_df.empty else 0

summary = {
    "dataset": config["dataset"],
    "rules_version": config["version"],
    "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "total_records": len(gdf),
    "rules_checked": len(rules),
    "total_issues": len(issues_df),
    "flagged_station_count": int(unique_flagged),
    "methodology_note": (
        "Independent project validation rules. "
        "Findings require context and do not "
        "necessarily indicate source-data errors."
    ),
    "rule_results": rule_results,
    "issues": [],
}

for row in issues:
    summary["issues"].append(
        {
            key: (json.loads(value) if key == "original_values" else value)
            for key, value in row.items()
        }
    )

json_file = WEB_DIR / "qc_results.json"

with open(json_file, "w", encoding="utf-8") as file:
    json.dump(summary, file, indent=2, allow_nan=False)


# ==================================================
# 7. EXPORT STATIONS FOR WEB MAP
# ==================================================

web_geojson = WEB_DIR / "sjrwmd_stations.geojson"

gdf.to_file(web_geojson, driver="GeoJSON")


# ==================================================
# 8. FINAL VALIDATION
# ==================================================

print("\nSJRWMD QUALITY REPORT")
print("--------------------------")
print("Stations checked:", len(gdf))
print("Rules:", len(rules))
print("Issue records:", len(issues_df))
print("Unique flagged stations:", unique_flagged)

print("\nSaved:")
print(csv_file)
print(json_file)
print(web_geojson)

print("\nOriginal source data was not modified.")
print("QA/QC processing complete.")
