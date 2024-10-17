from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.constants import ISO3S
from src.datasources import codab, floodscan
from src.utils import blob

LOCAL_DATA_DIR = Path("data/data")


def migrate_data_to_repo(clobber: bool = False):
    save_path = LOCAL_DATA_DIR / "adm.shp"
    if save_path.exists() and not clobber:
        return
    adms = []
    for iso3 in ISO3S:
        print(f"loading {iso3} adm to migrate")
        gdf_in = codab.load_codab_from_blob(iso3, admin_level=2)
        adms.append(gdf_in)
    adm = pd.concat(adms, ignore_index=True)
    adm.to_file(LOCAL_DATA_DIR / "adm.shp")


def load_data():
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
        blob_name = floodscan.get_blob_name(iso3, "exposure_tabular")
        df = blob.load_parquet_from_blob(blob_name)
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
    return data_out
