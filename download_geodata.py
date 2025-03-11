import geopandas as gpd
import pandas as pd

from constants import ADM_LEVELS, ISO3S, REGIONS
from utils import codab_utils


def clean_gdf(gdf, adm_level):
    gdf["name"] = gdf.apply(
        lambda row: (
            row[f"ADM{adm_level}_FR"]
            if pd.notna(row.get(f"ADM{adm_level}_FR"))
            and row.get(f"ADM{adm_level}_FR") != ""
            else row.get(f"ADM{adm_level}_EN", "")
        ),
        axis=1,
    )
    gdf.rename(columns={f"ADM{adm_level}_PCODE": "pcode"}, inplace=True)
    gdf = gdf[["pcode", "name", "geometry"]]
    return gdf


if __name__ == "__main__":
    region_gdfs = []
    for adm_level in ADM_LEVELS:
        print(f"Processing geo data for admin {adm_level}...")
        gdfs = []
        for iso3 in ISO3S:
            gdf = codab_utils.load_codab_from_blob(iso3, admin_level=adm_level)
            if (iso3 in ["nga", "tcd"]) and (adm_level == 0):
                gdf = gdf.dissolve()
            gdfs.append(gdf)
        gdf_all = pd.concat(gdfs)

        # aggregate relevant regions
        for region in REGIONS:
            if region["adm_level"] == adm_level:
                gdf_region_in = gdf_all[
                    gdf_all[f"ADM{adm_level}_PCODE"].isin(region["pcodes"])
                ]
                gdf_region_in = gdf_region_in.dissolve()
                gdf_region_in[
                    "pcode"
                ] = f'{region["iso3"]}_region_{region["region_number"]}'
                gdf_region_in["name"] = region["region_name"]
                gdf_region_in = gdf_region_in[["pcode", "name", "geometry"]]
                region_gdfs.append(gdf_region_in)

        if adm_level == 0:
            gdf_all_outline = gdf_all.copy()
            gdf_all_outline.geometry = gdf_all_outline.geometry.boundary
            gdf_all_outline = gpd.GeoDataFrame(
                gdf_all_outline, geometry="geometry"
            )
            gdf_all_outline = clean_gdf(gdf_all_outline, adm_level)
            gdf_all_outline.to_file(
                f"assets/geo/adm{adm_level}_outline.json", driver="GeoJSON"
            )

        gdf_all.geometry = gdf_all.geometry
        gdf_all = gpd.GeoDataFrame(gdf_all, geometry="geometry")
        gdf_all = clean_gdf(gdf_all, adm_level)

        gdf_all.to_file(f"assets/geo/adm{adm_level}.json", driver="GeoJSON")

    region_gdf = pd.concat(region_gdfs)
    region_gdf = gpd.GeoDataFrame(region_gdf, geometry="geometry")
    region_gdf.to_file("assets/geo/admregion.json", driver="GeoJSON")
    print("All data processed.")
