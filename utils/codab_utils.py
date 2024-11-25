import io
import zipfile
from typing import Literal

import geopandas as gpd
from azure.storage.blob import ContainerClient

from constants import DEV_BLOB_SAS, PROD_BLOB_SAS

PROJECT_PREFIX = "ds-floodexposure-monitoring"


def get_container_client(
    container_name: str = "projects", stage: Literal["prod", "dev"] = "dev"
):
    sas = DEV_BLOB_SAS if stage == "dev" else PROD_BLOB_SAS
    container_url = (
        f"https://imb0chd0{stage}.blob.core.windows.net/" f"{container_name}?{sas}"
    )
    return ContainerClient.from_container_url(container_url)


def load_blob_data(
    blob_name,
    stage: Literal["prod", "dev"] = "dev",
    container_name: str = "projects",
):
    container_client = get_container_client(stage=stage, container_name=container_name)
    blob_client = container_client.get_blob_client(blob_name)
    data = blob_client.download_blob().readall()
    return data


def load_gdf_from_blob(
    blob_name, shapefile: str = None, stage: Literal["prod", "dev"] = "dev"
):
    blob_data = load_blob_data(blob_name, stage=stage)
    with zipfile.ZipFile(io.BytesIO(blob_data), "r") as zip_ref:
        zip_ref.extractall("temp")
        if shapefile is None:
            shapefile = [f for f in zip_ref.namelist() if f.endswith(".shp")][0]
        gdf = gpd.read_file(f"temp/{shapefile}")
    return gdf


def get_blob_name(iso3: str):
    iso3 = iso3.lower()
    return f"{PROJECT_PREFIX}/raw/codab/{iso3}.shp.zip"


def load_codab_from_blob(iso3: str, admin_level: int = 0):
    iso3 = iso3.lower()
    shapefile = f"{iso3}_adm{admin_level}.shp"
    gdf = load_gdf_from_blob(
        blob_name=get_blob_name(iso3),
        shapefile=shapefile,
        stage="dev",
    )
    return gdf
