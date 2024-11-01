from pathlib import Path

import geopandas as gpd
import pandas as pd

from constants import ISO3S
from pipelines import blob_utils, codab_utils, floodscan_utils

LOCAL_DATA_DIR = Path("pipelines/data")


def migrate_data_to_repo(clobber: bool = False):
    save_path = LOCAL_DATA_DIR / "adm.shp"
    if save_path.exists() and not clobber:
        return
    adms = []
    for iso3 in ISO3S:
        print(f"loading {iso3} adm to migrate")
        gdf_in = codab_utils.load_codab_from_blob(iso3, admin_level=2)
        adms.append(gdf_in)
    adm = pd.concat(adms, ignore_index=True)
    adm.to_file(LOCAL_DATA_DIR / "adm.shp")


def load_data():
    print("Loading data...")
    migrate_data_to_repo()
    data_out = {}
    adm = gpd.read_file(LOCAL_DATA_DIR / "adm.shp")
    for adm_level in range(3):
        adm[f"ADM{adm_level}_NAME"] = adm[f"ADM{adm_level}_EN"].fillna(
            adm[f"ADM{adm_level}_FR"]
        )
    data_out["adm"] = adm

    def calculate_rolling(group, window=7):
        group[f"roll{window}"] = group["total_exposed"].rolling(window=window).mean()
        return group

    window = 7
    for iso3 in ISO3S:
        blob_name = floodscan_utils.get_blob_name(iso3, "exposure_tabular")
        df = blob_utils.load_parquet_from_blob(blob_name)
        df = df.merge(adm[["ADM1_PCODE", "ADM2_PCODE"]])
        df = df.sort_values("date")
        df = (
            df.groupby("ADM2_PCODE")
            .apply(calculate_rolling, window=window, include_groups=False)
            .reset_index(level=0)
        )
        df["dayofyear"] = df["date"].dt.dayofyear
        df["eff_date"] = pd.to_datetime(df["dayofyear"], format="%j")
        data_out[iso3] = df
    print("data loaded...")
    return data_out


if __name__ == "__main__":
    print("hello world!")
    data = load_data()
