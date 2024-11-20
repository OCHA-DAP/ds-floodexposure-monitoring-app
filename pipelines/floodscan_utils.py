from typing import Literal

from pipelines import blob_utils


def get_blob_name(
    iso3: str,
    data_type: Literal["exposure_raster", "exposure_tabular"],
    date: str = None,
):
    if data_type == "exposure_raster":
        if date is None:
            raise ValueError("date must be provided for exposure data")
        return (
            f"{blob_utils.PROJECT_PREFIX}/processed/flood_exposure/"
            f"{iso3}/{iso3}_exposure_{date}.tif"
        )
    elif data_type == "exposure_tabular":
        return (
            f"{blob_utils.PROJECT_PREFIX}/processed/flood_exposure/tabular/"
            f"{iso3}_adm_flood_exposure.parquet"
        )
    elif data_type == "flood_extent":
        return (
            f"{blob_utils.PROJECT_PREFIX}/processed/flood_extent/"
            f"{iso3}_flood_extent.tif"
        )
