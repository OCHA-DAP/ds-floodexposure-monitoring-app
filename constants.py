import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


ISO3S = ["ner", "nga", "cmr", "tcd", "bfa", "eth", "ssd", "som"]
ADMS = [0, 1, 2]

iso3_to_pcode = {
    "ner": "NE",
    "nga": "NG",
    "cmr": "CM",
    "tcd": "TD",
    "bfa": "BF",
    "eth": "ET",
    "ssd": "SS",
    "som": "SO",
}

pcode_to_iso3 = {
    "NE": "ner",
    "NG": "nga",
    "CM": "cmr",
    "TD": "tcd",
    "BF": "bfa",
    "ET": "eth",
    "SS": "ssd",
    "SO": "som",
}

CHD_GREEN = "#1bb580"

NAVBAR_HEIGHT = 60

AZURE_DB_PW_DEV = os.getenv("AZURE_DB_PW_DEV")
AZURE_DB_UID = os.getenv("AZURE_DB_UID")

PROD_BLOB_SAS = os.getenv("PROD_BLOB_SAS")
DEV_BLOB_SAS = os.getenv("DEV_BLOB_SAS")

engine = create_engine(
    f"postgresql+psycopg2://{AZURE_DB_UID}:{AZURE_DB_PW_DEV}@chd-rasterstats-dev.postgres.database.azure.com/postgres"  # noqa
)

ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'  # noqa
URL = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
URL_LABELS = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png"
