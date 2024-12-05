import time

import pandas as pd
from sqlalchemy import text
from utils.log_utils import get_logger

logger = get_logger("data")


def fetch_flood_data(engine, pcode, adm_level):
    """Fetch flood exposure and administrative data from database."""
    query_exposure = text(
        """
        SELECT *
        FROM app.floodscan_exposure
        WHERE pcode=:pcode AND adm_level=:adm_level
        """
    )
    query_adm = text("select * from app.adm")
    logger.info(f"Getting flood exposure data for {pcode}...")
    start = time.time()
    with engine.connect() as con:
        df_exposure = pd.read_sql_query(
            query_exposure,
            con,
            params={"pcode": pcode, "adm_level": adm_level},
        )
        df_adm = pd.read_sql_query(query_adm, con)
        df_adm = df_adm[df_adm[f"adm{adm_level}_pcode"] == pcode]

    elapsed = time.time() - start
    logger.debug(
        f"Retrieved {len(df_exposure)} rows from database in {elapsed:.2f}s"
    )
    return df_exposure, df_adm


def process_flood_data(df_exposure, window=7):
    """Process flood data for visualization."""
    df_exposure = df_exposure.rename(columns={"valid_date": "date"})
    df_exposure = df_exposure.sort_values("date")

    val_col = f"roll{window}"

    # Calculate rolling averages
    df_exposure[val_col] = df_exposure["sum"].rolling(window).mean()

    # Calculate seasonal averages
    df_exposure["date"] = pd.to_datetime(df_exposure["date"])
    df_exposure["dayofyear"] = df_exposure["date"].dt.dayofyear
    df_seasonal = (
        df_exposure[df_exposure["date"].dt.year < 2024]
        .groupby("dayofyear")[val_col]
        .mean()
        .reset_index()
    )
    df_seasonal["eff_date"] = pd.to_datetime(
        df_seasonal["dayofyear"], format="%j"
    )

    # Filter data
    today_dayofyear = df_exposure.iloc[-1]["dayofyear"]
    df_to_today = df_exposure[df_exposure["dayofyear"] <= today_dayofyear]

    # Calculate peaks
    df_peaks = (
        df_to_today.groupby(df_to_today["date"].dt.year)[val_col]
        .max()
        .reset_index()
    )

    df_exposure["eff_date"] = pd.to_datetime(
        df_exposure["dayofyear"], format="%j"
    )
    return df_exposure, df_seasonal, df_peaks


def calculate_return_periods(df_peaks, rp: int = 3, window: int = 7):
    """Calculate return periods for flood events."""
    df_peaks["rank"] = df_peaks[f"roll{window}"].rank(ascending=False)
    df_peaks["rp"] = (len(df_peaks) + 1) / df_peaks["rank"]
    df_peaks[f"{rp}yr_rp"] = df_peaks["rp"] >= rp
    peak_years = df_peaks[df_peaks[f"{rp}yr_rp"]]["date"].to_list()
    return df_peaks.sort_values(by="rp"), peak_years


def get_summary(df_exposure, df_adm, adm_level, window=7):
    name = df_adm.iloc[0][f"adm{adm_level}_name"]
    max_date = f"{df_exposure['date'].max():%Y-%m-%d}"
    val_col = f"roll{window}"

    df_ = df_exposure[df_exposure["date"] == max_date]

    people_exposed = int(
        df_.groupby([f"adm{adm_level}_pcode"])[val_col]
        .sum()
        .reset_index()
        .iloc[0][val_col]
    )
    people_exposed_formatted = "{:,}".format(people_exposed)

    return (
        name,
        f"{people_exposed_formatted} people exposed to flooding as of {max_date}.",
    )
