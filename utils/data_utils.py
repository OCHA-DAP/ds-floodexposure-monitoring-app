import time
from typing import Literal

import pandas as pd
from dash import dcc
from sqlalchemy import create_engine, text

from constants import (
    AZURE_DB_BASE_URL,
    AZURE_DB_PW_DEV,
    AZURE_DB_PW_PROD,
    AZURE_DB_UID,
    CUR_YEAR,
    ROLLING_WINDOW,
    STAGE,
)
from utils.log_utils import get_logger

logger = get_logger("data")


def get_engine(stage: Literal["dev", "prod"] = "dev"):
    logger.debug(f"Connecting to {stage} database")
    if stage == "dev":
        url = AZURE_DB_BASE_URL.format(
            uid=AZURE_DB_UID, pw=AZURE_DB_PW_DEV, db_name="chd-rasterstats-dev"
        )
    elif stage == "prod":
        url = AZURE_DB_BASE_URL.format(
            uid=AZURE_DB_UID,
            pw=AZURE_DB_PW_PROD,
            db_name="chd-rasterstats-prod",
        )
    else:
        raise ValueError(f"Invalid stage: {stage}")
    return create_engine(url)


def fetch_flood_data(pcode, adm_level):
    """Fetch flood exposure and administrative data from database."""
    flood_table = (
        "floodscan_exposure_regions"
        if adm_level == "region"
        else "floodscan_exposure"
    )

    query_exposure = text(
        f"""
        SELECT *
        FROM app.{flood_table}
        WHERE pcode=:pcode AND adm_level=:adm_level
        """
    )
    params = {"pcode": pcode, "adm_level": adm_level}
    query_adm = text("select * from app.adm")
    logger.info(f"Getting flood exposure data for {pcode}...")
    start = time.time()
    engine = get_engine(STAGE)
    with engine.connect() as con:
        df_exposure = pd.read_sql_query(
            query_exposure,
            con,
            params=params,
        )
        df_adm = pd.read_sql_query(query_adm, con)
        df_adm = df_adm[df_adm[f"adm{adm_level}_pcode"] == pcode]

    elapsed = time.time() - start
    logger.debug(
        f"Retrieved {len(df_exposure)} rows from database in {elapsed:.2f}s"  # noqa
    )
    return df_exposure, df_adm


def process_flood_data(df_exposure):
    """Process flood data for visualization."""
    df_exposure = df_exposure.rename(columns={"valid_date": "date"})
    df_exposure = df_exposure.sort_values("date")

    val_col = f"roll{ROLLING_WINDOW}"

    # Calculate rolling averages
    df_exposure[val_col] = df_exposure["sum"].rolling(ROLLING_WINDOW).mean()

    # Calculate seasonal averages
    df_exposure["date"] = pd.to_datetime(df_exposure["date"])
    df_exposure["dayofyear"] = df_exposure["date"].dt.dayofyear
    df_seasonal = (
        df_exposure[df_exposure["date"].dt.year < CUR_YEAR]
        .groupby("dayofyear")[val_col]
        .median()
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


def calculate_return_periods(df_peaks, rp: int = 3):
    """Calculate return periods for flood events."""
    df_peaks["rank"] = df_peaks[f"roll{ROLLING_WINDOW}"].rank(ascending=False)
    df_peaks["rp"] = (len(df_peaks) + 1) / df_peaks["rank"]
    df_peaks[f"{rp}yr_rp"] = df_peaks["rp"] >= rp
    peak_years = df_peaks[df_peaks[f"{rp}yr_rp"]]["date"].to_list()
    return df_peaks.sort_values(by="rp"), peak_years


def get_current_quantiles(adm_level):
    quantile_table = (
        "current_quantile_regions"
        if adm_level == "region"
        else "current_quantile"
    )

    engine = get_engine(STAGE)
    query = text(
        f"""
        select * from app.{quantile_table}
        where adm_level=:adm_level
        """
    )
    with engine.connect() as con:
        df = pd.read_sql_query(query, con, params={"adm_level": adm_level})
    return df


def get_summary(df_exposure, df_adm, adm_level, quantile):
    name = df_adm.iloc[0][f"adm{adm_level}_name"]
    adm0_name = df_adm.iloc[0]["adm0_name"]
    max_date = f"{df_exposure['date'].max():%b %d, %Y}"  # noqa
    val_col = f"roll{ROLLING_WINDOW}"

    df_ = df_exposure[df_exposure["date"] == max_date]

    people_exposed = int(
        df_.groupby([f"adm{adm_level}_pcode"])[val_col]
        .sum()
        .reset_index()
        .iloc[0][val_col]
    )
    people_exposed_formatted = "{:,}".format(people_exposed)

    quantile_label = {
        -2: "well below normal",
        -1: "below normal",
        0: "normal",
        1: "above normal",
        2: "well above normal",
    }

    summary_text = dcc.Markdown(
        f"""
        **{people_exposed_formatted}** people exposed to flooding as of **{max_date}**.

        This is **{quantile_label[quantile]}** for this day of the year.
        """
    )
    name = name if adm_level == "0" else f"{name}, {adm0_name}"
    return (name, summary_text)
