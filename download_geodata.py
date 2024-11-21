import json
import os
from typing import Literal

from azure.storage.blob import ContainerClient
from dotenv import load_dotenv

load_dotenv()

PROD_BLOB_SAS = os.getenv("PROD_BLOB_SAS")
DEV_BLOB_SAS = os.getenv("DEV_BLOB_SAS")
CONTAINER = "projects"


def download_geojson_from_azure(
    container_client,
    blob_name,
    output_path,
):
    """
    Download a GeoJSON file from Azure Blob Storage using a SAS token.

    Parameters:
    -----------
    container_client : azure.storage.blob.ContainerClient
        Azure ContainerClient
    blob_name : str
        Name of the blob to download
    output_path : str, optional
        Path where to save the GeoJSON file.
    """
    print(f"Getting data for {blob_name}")
    blob_client = container_client.get_blob_client(blob_name)
    blob_data = blob_client.download_blob()
    geojson_str = blob_data.readall().decode("utf-8")
    geojson_data = json.loads(geojson_str)
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(geojson_data, f)
        print(f"GeoJSON saved to: {output_path}")


def get_container_client(
    container_name: str = "projects", stage: Literal["prod", "dev"] = "dev"
):
    sas = DEV_BLOB_SAS if stage == "dev" else PROD_BLOB_SAS
    container_url = (
        f"https://imb0chd0{stage}.blob.core.windows.net/"  # noqa
        f"{container_name}?{sas}"  # noqa
    )
    return ContainerClient.from_container_url(container_url)


if __name__ == "__main__":
    container_client = get_container_client(CONTAINER)
    blob_name = "my_spatial_data.geojson"
    blobs = container_client.list_blobs(
        name_starts_with="ds-floodexposure-monitoring/processed/geojson"
    )

    for blob in blobs:
        blob_name = blob.name
        if blob_name.endswith(".json"):
            output_name = blob_name.split("/")[-1]
            print(output_name)

            gdf = download_geojson_from_azure(
                container_client=container_client,
                blob_name=blob_name,
                output_path=f"assets/geo/{output_name}",
            )
