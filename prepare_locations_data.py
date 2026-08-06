"""Clean the raw locations CSV and upload it to Azure Blob Storage.

Source columns are mislabeled ("Point - Latitude" actually holds
longitude values and vice versa) and include ~1,547 rows with no
coordinates at all - both are fixed here, once, rather than on every
app cold-start. Only the columns the app actually needs are kept.
Re-runnable and idempotent.
"""

import ocha_stratus as stratus
import pandas as pd

from constants import LOCATIONS_BLOB_NAME, STAGE

SOURCE_CSV = "sudan_locations_demo.csv"


def prepare_locations_df():
    df = pd.read_csv(SOURCE_CSV, encoding="utf-8-sig")
    df = df.rename(
        columns={
            "Point - Longitude": "lat",
            "Point - Latitude": "lon",
            "Name": "name",
            "Site Type Reference Label": "site_type",
        }
    )
    df = df[df["lat"].notna() & df["lon"].notna()]
    df = df[["name", "site_type", "lat", "lon"]].copy()
    df["lat"] = df["lat"].round(5)
    df["lon"] = df["lon"].round(5)
    return df.reset_index(drop=True)


if __name__ == "__main__":
    df = prepare_locations_df()
    stratus.upload_parquet_to_blob(df, LOCATIONS_BLOB_NAME, stage=STAGE)
    print(
        f"Uploaded {len(df)} locations to {LOCATIONS_BLOB_NAME} (stage={STAGE})."
    )
