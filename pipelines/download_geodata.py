import os

import geopandas as gpd
import ocha_stratus as ocha
import pandas as pd
import yaml

STAGE = os.getenv("STAGE")
PROJECT_PREFIX = "ds-floodexposure-monitoring"


def get_blob_name(iso3: str):
    iso3 = iso3.lower()
    return f"{PROJECT_PREFIX}/raw/codab/{iso3}.shp.zip"


def load_codab_from_blob(iso3: str, admin_level: int = 0):
    iso3 = iso3.lower()
    shapefile = f"{iso3}_adm{admin_level}.shp"
    gdf = ocha.load_shp_from_blob(
        blob_name=get_blob_name(iso3),
        shapefile=shapefile,
        stage=STAGE,
    )
    return gdf


def clean_gdf(gdf):
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


def load_geo_data(iso3s, regions, save_to_database=True):
    """Load geo data from blob storage and save to database."""
    adms = []
    for iso3 in iso3s:
        print(f"loading {iso3} adm to migrate")
        gdf_in = load_codab_from_blob(iso3, admin_level=2)
        adms.append(gdf_in)
    adm = pd.concat(adms, ignore_index=True)

    for adm_level in range(3):
        adm[f"ADM{adm_level}_NAME"] = adm[f"ADM{adm_level}_FR"].fillna(
            adm[f"ADM{adm_level}_EN"]
        )
    adm.drop(columns=["geometry"], inplace=True)
    adm.columns = adm.columns.str.lower()

    region_dicts = []
    for region in regions:
        adm_names = adm[
            adm[f"adm{region['adm_level']}_pcode"].isin(region["pcodes"])
        ][f"adm{region['adm_level']}_name"].unique()
        region_dicts.append(
            {
                "admregion_pcode": f'{region["iso3"]}_region_{region["region_number"]}',
                "admregion_name": f'{region["region_name"]} ({", ".join(adm_names)})',
            }
        )

    df_out = pd.concat([adm, pd.DataFrame(region_dicts)], ignore_index=True)

    if save_to_database:
        df_out.to_sql(
            "admin_lookup",
            schema="app",
            con=ocha.get_engine(STAGE, write=True),
            if_exists="replace",
            index=False,
        )


if __name__ == "__main__":
    # Check the env vars are defined properly
    if STAGE == "prod":
        blob_sas = os.environ.get("DSCI_AZ_BLOB_PROD_SAS")
        db_password = os.environ.get("DSCI_AZ_DB_PROD_PW_WRITE")
        db_username = os.environ.get("DSCI_AZ_DB_PROD_UID_WRITE")
    else:
        blob_sas = os.environ.get("DSCI_AZ_BLOB_DEV_SAS")
        db_password = os.environ.get("DSCI_AZ_DB_DEV_PW_WRITE")
        db_username = os.environ.get("DSCI_AZ_DB_DEV_UID_WRITE")

    # Check if we have the required credentials
    if not blob_sas or not db_password or not db_username:
        raise ValueError(
            f"Missing credentials for {STAGE} environment. Please check GitHub secrets."
        )

    with open("pipelines/config.yml", "r") as f:
        config = yaml.safe_load(f)

    iso3s = config["iso3s"]
    regions = config["regions"]
    adm_levels = config["adm_levels"]

    load_geo_data(iso3s, regions)

    print(iso3s)
    print(regions)

    region_gdfs = []
    for adm_level in adm_levels:
        print(f"Processing geo data for admin {adm_level}...")
        gdfs = []
        for iso3 in iso3s:
            gdf = load_codab_from_blob(iso3, admin_level=adm_level)
            if (iso3 in ["nga", "tcd"]) and (adm_level == 0):
                gdf = gdf.dissolve()
            gdfs.append(gdf)
        gdf_all = pd.concat(gdfs)

        # aggregate relevant regions
        for region in regions:
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
            gdf_all_outline = clean_gdf(gdf_all_outline)
            gdf_all_outline.to_file(
                f"assets/geo/adm{adm_level}_outline.json", driver="GeoJSON"
            )

        gdf_all.geometry = gdf_all.geometry
        gdf_all = gpd.GeoDataFrame(gdf_all, geometry="geometry")
        gdf_all = clean_gdf(gdf_all)

        gdf_all.to_file(f"assets/geo/adm{adm_level}.json", driver="GeoJSON")

    region_gdf = pd.concat(region_gdfs)
    region_gdf = gpd.GeoDataFrame(region_gdf, geometry="geometry")
    region_gdf.to_file("assets/geo/admregion.json", driver="GeoJSON")
    print("All data processed.")
