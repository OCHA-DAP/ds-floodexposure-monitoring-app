import pandas as pd
from sqlalchemy import text


def fetch_flood_data(engine, pcode, adm_level):
    """Fetch flood exposure and administrative data from database."""
    query_exposure = text(
        f"select * from app.flood_exposure where adm{adm_level}_pcode=:pcode"
    )
    query_adm = text("select * from app.adm")

    with engine.connect() as con:
        df_exposure = pd.read_sql_query(query_exposure, con, params={"pcode": pcode})
        df_adm = pd.read_sql_query(query_adm, con)
        df_adm = df_adm[df_adm[f"adm{adm_level}_pcode"] == pcode]

    return df_exposure, df_adm


def process_flood_data(df_exposure, pcode, adm_level, window=7):
    """Process flood data for visualization."""
    val_col = f"roll{window}"

    # Calculate seasonal averages
    df_seasonal = (
        df_exposure[df_exposure["date"].dt.year < 2024]
        .groupby(["adm1_pcode", "adm2_pcode", "dayofyear"])[val_col]
        .mean()
        .reset_index()
    )
    df_seasonal["eff_date"] = pd.to_datetime(df_seasonal["dayofyear"], format="%j")

    # Filter data
    today_dayofyear = df_exposure.iloc[-1]["dayofyear"]
    df_to_today = df_exposure[df_exposure["dayofyear"] <= today_dayofyear]

    # Calculate peaks
    df_peaks = (
        df_to_today.groupby([df_to_today["date"].dt.year, "adm1_pcode", "adm2_pcode"])[
            val_col
        ]
        .max()
        .reset_index()
    )

    # Aggregate by admin level
    aggregation_funcs = {
        "0": lambda d, s, p: (
            d.groupby(["dayofyear", "date"])[val_col].sum().reset_index(),
            s.groupby("eff_date")[val_col].sum().reset_index(),
            p.groupby("date")[val_col].sum().reset_index(),
        ),
        "1": lambda d, s, p: (
            d[d["adm1_pcode"] == pcode]
            .groupby(["dayofyear", "date"])[val_col]
            .sum()
            .reset_index(),
            s[s["adm1_pcode"] == pcode]
            .groupby("eff_date")[val_col]
            .sum()
            .reset_index(),
            p[p["adm1_pcode"] == pcode].groupby("date")[val_col].sum().reset_index(),
        ),
        "2": lambda d, s, p: (
            d[d["adm2_pcode"] == pcode],
            s[s["adm2_pcode"] == pcode],
            p[p["adm2_pcode"] == pcode].copy(),
        ),
    }

    df_processed, df_seasonal_final, df_peaks_final = aggregation_funcs[adm_level](
        df_exposure, df_seasonal, df_peaks
    )
    df_processed["eff_date"] = pd.to_datetime(df_processed["dayofyear"], format="%j")

    return df_processed, df_seasonal_final, df_peaks_final


def calculate_return_periods(df_peaks, rp=3):
    """Calculate return periods for flood events."""
    df_peaks["rank"] = df_peaks["roll7"].rank(ascending=False)
    df_peaks["rp"] = len(df_peaks) / df_peaks["rank"]
    df_peaks[f"{rp}yr_rp"] = df_peaks["rp"] >= rp
    peak_years = df_peaks[df_peaks[f"{rp}yr_rp"]]["date"].to_list()
    return df_peaks.sort_values(by="rp"), peak_years
