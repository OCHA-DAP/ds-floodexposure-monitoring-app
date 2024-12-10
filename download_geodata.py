import geopandas as gpd
import pandas as pd

from constants import ADMS, ISO3S
from utils import codab_utils, data_utils


def clean_gdf(gdf):
    gdf["name"] = gdf.apply(
        lambda row: (
            row[f"ADM{adm}_FR"]
            if pd.notna(row.get(f"ADM{adm}_FR"))
            and row.get(f"ADM{adm}_FR") != ""
            else row.get(f"ADM{adm}_EN", "")
        ),
        axis=1,
    )
    gdf.rename(columns={f"ADM{adm}_PCODE": "pcode"}, inplace=True)
    gdf = gdf[["pcode", "name", "geometry"]]
    return gdf


def load_geo_data(save_to_database=True):
    """Load geo data from blob storage and save to database."""
    adms = []
    for iso3 in ISO3S:
        print(f"loading {iso3} adm to migrate")
        gdf_in = codab_utils.load_codab_from_blob(iso3, admin_level=2)
        adms.append(gdf_in)
    adm = pd.concat(adms, ignore_index=True)

    for adm_level in range(3):
        adm[f"ADM{adm_level}_NAME"] = adm[f"ADM{adm_level}_FR"].fillna(
            adm[f"ADM{adm_level}_FR"]
        )
    adm.drop(columns=["geometry"], inplace=True)
    adm.columns = adm.columns.str.lower()
    if save_to_database:
        adm.to_sql(
            "adm",
            schema="app",
            con=data_utils.get_engine(stage="dev"),
            if_exists="replace",
            index=False,
        )


if __name__ == "__main__":
    load_geo_data()
    for adm in ADMS:
        print(f"Processing geo data for admin {adm}...")
        gdfs = []
        for iso3 in ISO3S:
            gdf = codab_utils.load_codab_from_blob(iso3, admin_level=adm)
            if (iso3 in ["nga", "tcd"]) and (adm == 0):
                gdf = gdf.dissolve()
            gdfs.append(gdf)
        gdf_all = pd.concat(gdfs)
        if adm == 0:
            gdf_all_outline = gdf_all.copy()
            gdf_all_outline.geometry = gdf_all_outline.geometry.boundary
            gdf_all_outline = gpd.GeoDataFrame(
                gdf_all_outline, geometry="geometry"
            )
            gdf_all_outline = clean_gdf(gdf_all_outline)
            gdf_all_outline.to_file(
                f"assets/geo/adm{adm}_outline.json", driver="GeoJSON"
            )

        gdf_all.geometry = gdf_all.geometry
        gdf_all = gpd.GeoDataFrame(gdf_all, geometry="geometry")
        gdf_all = clean_gdf(gdf_all)

        gdf_all.to_file(f"assets/geo/adm{adm}.json", driver="GeoJSON")
    print("All data processed.")
