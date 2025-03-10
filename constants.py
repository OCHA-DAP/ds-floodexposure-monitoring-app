import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()

ROLLING_WINDOW = 7

CHD_GREEN = "#1bb580"
CHD_BLUE = "#007ce0"
CHD_LIGHTBLUE = "#66b0ec"
CHD_GREY = "#888888"
CHD_MINT = "#1ebfb3"
CHD_RED = "#f2645a"

NAVBAR_HEIGHT = 60

PROD_BLOB_SAS = os.getenv("DSCI_AZ_BLOB_PROD_SAS")
DEV_BLOB_SAS = os.getenv("DSCI_AZ_BLOB_DEV_SAS")

ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'  # noqa
URL = "https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png"
URL_LABELS = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png"

CUR_YEAR = datetime.today().year

STAGE = os.getenv("STAGE")
