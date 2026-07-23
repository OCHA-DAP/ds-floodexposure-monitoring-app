"""Filter the generated GeoJSON assets down to a single country.

This app is scoped to Sudan only. The GeoJSON files produced by
``download_geodata.py`` contain every country in ``ISO3S``; this script
keeps only the features whose pcode matches the target country and
rewrites the files in place. Re-runnable and idempotent.
"""

import json

from constants import iso3_to_pcode

TARGET_ISO3 = "sdn"
TARGET_PCODE_PREFIX = iso3_to_pcode[TARGET_ISO3]

GEO_FILES = [
    "assets/geo/adm0.json",
    "assets/geo/adm1.json",
    "assets/geo/adm2.json",
    "assets/geo/adm0_outline.json",
]


def filter_file(path, prefix):
    with open(path, "r") as f:
        data = json.load(f)

    before = len(data["features"])
    data["features"] = [
        feature
        for feature in data["features"]
        if feature["properties"].get("pcode", "").startswith(prefix)
    ]
    after = len(data["features"])

    with open(path, "w") as f:
        json.dump(data, f)

    print(f"{path}: {before} -> {after} features")


if __name__ == "__main__":
    for geo_file in GEO_FILES:
        filter_file(geo_file, TARGET_PCODE_PREFIX)
    print(f"Filtered geodata to {TARGET_ISO3} ({TARGET_PCODE_PREFIX}).")
