from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.constants import ISO3S
from src.datasources import codab

LOCAL_DATA_DIR = Path("data/data")


def migrate_data_to_repo(clobber: bool = False):
    save_path = LOCAL_DATA_DIR / "adm.shp"
    if save_path.exists() and not clobber:
        return
    adms = []
    for iso3 in ISO3S:
        print(f"loading {iso3} adm")
        gdf_in = codab.load_codab_from_blob(iso3, admin_level=2)
        adms.append(gdf_in)
    adm = pd.concat(adms, ignore_index=True)
    adm.to_file(LOCAL_DATA_DIR / "adm.shp")


def load_data():
    migrate_data_to_repo()
    adm = gpd.read_file(LOCAL_DATA_DIR / "adm.shp")
    return {"adm": adm}
