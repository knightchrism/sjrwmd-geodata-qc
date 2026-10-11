
from pathlib import Path
import json
import csv

PROJECT_DIR = Path(__file__).resolve().parent

METADATA_FILE = (
    PROJECT_DIR / "data" / "raw" /
    "sjrwmd_service_metadata.json"
)

OUTPUT_FILE = (
    PROJECT_DIR / "reports" /
    "sjrwmd_data_dictionary.csv"
)

RULES_FILE = (
    PROJECT_DIR / "config" / "qc_rules.json"
)

with open(METADATA_FILE, encoding="utf-8") as file:
    metadata = json.load(file)

with open(RULES_FILE, encoding="utf-8") as file:
    config = json.load(file)

# Tentative source-system groupings.
# These are hypotheses, not verified field lineage.
station_fields = {
    "STN_ID", "STN_NM", "STN_TYPE", "STN_CTGRY",
    "LAT_NO_DD", "LONG_NO_DD", "UTM_X", "UTM_Y",
    "COUNTY", "HORZ_CTL_DTM"
}

well_fields = {
    "WELL_DRL_DPTH_QTY", "CUR_WELL_DPTH_QTY",
    "TOTL_WELL_CSNG_DPTH_QTY", "NOMNL_CSNG_DMTR_QTY",
    "BOTTOM_HOLE_ELEV", "CASED_HOLE_ELEV"
}

monitoring_fields = {
    "SDMS_MON_STTS", "EVENT_TYPE", "FREQ",
    "COLL_AGNCY", "STTS_DT"
}


def possible_source(field_name):
    if field_name in station_fields:
        return "Station Header (tentative)"
    if field_name in well_fields:
        return "WCL (tentative)"
    if field_name in monitoring_fields:
        return "SDMS (tentative)"
    return "Unverified"


def related_rules(field_name):
    matches = []

    for rule in config["rules"]:
        fields = rule.get("fields", [rule.get("field")])

        if field_name in fields:
            matches.append(rule["id"])

    return ", ".join(matches)


records = []

for field in metadata.get("fields", []):
    name = field["name"]

    records.append({
        "field_name": name,
        "alias": field.get("alias", ""),
        "arcgis_type": field.get("type", ""),
        "nullable": field.get("nullable", ""),
        "length": field.get("length", ""),
        "possible_source_model": possible_source(name),
        "source_model_verified": "No",
        "related_qc_rules": related_rules(name),
        "notes": ""
    })

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8-sig"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "field_name",
            "alias",
            "arcgis_type",
            "nullable",
            "length",
            "possible_source_model",
            "source_model_verified",
            "related_qc_rules",
            "notes"
        ]
    )

    writer.writeheader()
    writer.writerows(records)

print("Data dictionary generated!")
print("Fields documented:", len(records))
print("File:", OUTPUT_FILE)
print("Source-model assignments are tentative.")
