import io
import os
import zipfile
from typing import Literal

import geopandas as gpd
import pandas as pd
from azure.storage.blob import ContainerClient

PROD_BLOB_SAS = os.getenv("PROD_BLOB_SAS")
DEV_BLOB_SAS = os.getenv("DEV_BLOB_SAS")

PROJECT_PREFIX = "ds-floodexposure-monitoring"


def get_container_client(
    container_name: str = "projects", stage: Literal["prod", "dev"] = "dev"
):
    sas = DEV_BLOB_SAS if stage == "dev" else PROD_BLOB_SAS
    container_url = (
        f"https://imb0chd0{stage}.blob.core.windows.net/" f"{container_name}?{sas}"
    )
    return ContainerClient.from_container_url(container_url)


def load_parquet_from_blob(
    blob_name,
    stage: Literal["prod", "dev"] = "dev",
    container_name: str = "projects",
):
    blob_data = load_blob_data(blob_name, stage=stage, container_name=container_name)
    return pd.read_parquet(io.BytesIO(blob_data))


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


def load_blob_data(
    blob_name,
    stage: Literal["prod", "dev"] = "dev",
    container_name: str = "projects",
):
    container_client = get_container_client(stage=stage, container_name=container_name)
    blob_client = container_client.get_blob_client(blob_name)
    data = blob_client.download_blob().readall()
    return data
