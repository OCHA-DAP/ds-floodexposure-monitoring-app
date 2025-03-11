import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


ISO3S = [
    "ner",
    "nga",
    "cmr",
    "tcd",
    "bfa",
    "eth",
    "ssd",
    "som",
    "mli",
    "cod",
    "moz",
    "mwi",
]
ADM_LEVELS = [0, 1, 2]

ROLLING_WINDOW = 7

iso3_to_pcode = {
    "ner": "NE",
    "nga": "NG",
    "cmr": "CM",
    "tcd": "TD",
    "bfa": "BF",
    "eth": "ET",
    "ssd": "SS",
    "som": "SO",
    "mli": "ML",
    "cod": "CD",
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
    "ML": "mli",
    "CD": "cod",
}

# specific pcodes for building regions
NORDKIVU1 = "CD61"
SUDKIVU1 = "CD62"
TANGANYIKA1 = "CD74"
BASUELE1 = "CD52"
HAUTUELE1 = "CD53"
TSHOPO1 = "CD51"

REGIONS = [
    {
        "adm_level": 1,
        "iso3": "cod",
        "region_number": 1,
        "region_name": "Zone 1",
        "pcodes": [BASUELE1, HAUTUELE1, TSHOPO1],
    },
    {
        "adm_level": 1,
        "iso3": "cod",
        "region_number": 2,
        "region_name": "Zone 2",
        "pcodes": [NORDKIVU1, SUDKIVU1],
    },
    {
        "adm_level": 1,
        "iso3": "cod",
        "region_number": 3,
        "region_name": "Zone 3",
        "pcodes": [TANGANYIKA1],
    },
]

CHD_GREEN = "#1bb580"
CHD_BLUE = "#007ce0"
CHD_LIGHTBLUE = "#66b0ec"
CHD_GREY = "#888888"
CHD_MINT = "#1ebfb3"
CHD_RED = "#f2645a"

NAVBAR_HEIGHT = 60

ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'  # noqa
URL = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
URL_LABELS = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png"

CUR_YEAR = datetime.today().year

STAGE = os.getenv("STAGE")
