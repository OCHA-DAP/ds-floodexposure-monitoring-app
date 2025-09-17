import geopandas as gpd
from fsspec.implementations.http import HTTPFileSystem

from constants import ISO3S

GEOPARQUET_URLS = {
    0: "https://data.fieldmaps.io/adm0/osm/intl/adm0_polygons.parquet",
    1: "https://data.fieldmaps.io/edge-matched/humanitarian/intl/adm1_polygons.parquet",
    2: "https://data.fieldmaps.io/edge-matched/humanitarian/intl/adm2_polygons.parquet",
}


if __name__ == "__main__":
    for adm_level in [0, 1, 2]:
        url = GEOPARQUET_URLS[adm_level]

        # Get as a geodataframe
        iso3s = [iso3.upper() for iso3 in ISO3S]
        filters = [("iso_3", "in", iso3s)]
        filesystem = HTTPFileSystem()
        gdf = gpd.read_parquet(url, filters=filters, filesystem=filesystem)

        # Select columns and rename
        gdf = gdf[[f"adm{adm_level}_name1", f"adm{adm_level}_src", "geometry"]]
        gdf = gdf.rename(
            columns={
                f"adm{adm_level}_name1": "name",
                f"adm{adm_level}_src": "pcode",
            }
        )

        # Simplify geometry and save
        gdf["geometry"] = gdf.geometry.simplify(tolerance=0.005)

        if adm_level == 0:
            gdf_outline = gdf.copy()
            gdf_outline.geometry = gdf_outline.geometry.boundary
            gdf_outline = gpd.GeoDataFrame(gdf_outline, geometry="geometry")
            gdf_outline.to_file(
                f"assets/geo/adm{adm_level}_outline.json", driver="GeoJSON"
            )
        gdf.to_file(f"assets/geo/adm{adm_level}.json", driver="GeoJSON")

    print("All data processed.")
