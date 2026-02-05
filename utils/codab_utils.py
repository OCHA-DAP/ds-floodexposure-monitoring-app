from typing import Literal

import ocha_stratus as stratus

from constants import STAGE

PROJECT_PREFIX = "ds-floodexposure-monitoring"


def load_blob_data(
    blob_name,
    stage: Literal["prod", "dev"] = "dev",
    container_name: str = "projects",
):
    container_client = stratus.get_container_client(
        stage=stage, container_name=container_name
    )
    blob_client = container_client.get_blob_client(blob_name)
    data = blob_client.download_blob().readall()
    return data


def get_blob_name(iso3: str):
    iso3 = iso3.lower()
    return f"{PROJECT_PREFIX}/raw/codab/{iso3}.shp.zip"


def load_codab_from_blob(iso3: str, admin_level: int = 0):
    iso3 = iso3.lower()
    shapefile = f"{iso3}_adm{admin_level}.shp"
    gdf = stratus.load_shp_from_blob(
        blob_name=get_blob_name(iso3),
        shapefile=shapefile,
        stage=STAGE,
    )
    return gdf
