import os

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()


ISO3S = ["ner", "nga", "cmr", "tcd", "bfa", "eth"]

iso3_to_pcode = {
    "ner": "NE",
    "nga": "NG",
    "cmr": "CM",
    "tcd": "TD",
    "bfa": "BF",
    "eth": "ET",
}

pcode_to_iso3 = {
    "NE": "ner",
    "NG": "nga",
    "CM": "cmr",
    "TD": "tcd",
    "BF": "bfa",
    "ET": "eth",
}

CHD_GREEN = "#1bb580"

NAVBAR_HEIGHT = 60

AZURE_DB_PW_DEV = os.getenv("AZURE_DB_PW_DEV")
AZURE_DB_UID = os.getenv("AZURE_DB_UID")
engine = create_engine(
    f"postgresql+psycopg2://{AZURE_DB_UID}:{AZURE_DB_PW_DEV}@chd-rasterstats-dev.postgres.database.azure.com/postgres"
)

ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
URL = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
