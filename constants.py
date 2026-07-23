import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()


# This app is scoped to Sudan only.
ISO3S = [
    "sdn",
]
ADM_LEVELS = [0, 1, 2]

# Map view centered on Sudan
MAP_CENTER = [15.9, 30.2]
MAP_ZOOM = 5

ROLLING_WINDOW = int(os.getenv("ROLL_WINDOW", 7))

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
    "sdn": "SD",
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
    "SD": "sdn",
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
OCHA_BLUE = "#0072BC"
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
