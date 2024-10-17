import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output

from src.constants import CHD_GREEN, iso3_to_pcode


def register_callbacks(app):
    @app.callback(
        Output("adm1", "options"),
        Output("adm1", "value"),
        Output("adm1", "disabled"),
        Input("adm_level", "value"),
        Input("iso3", "value"),
    )
    def update_adm1_dropdown(adm_level, iso3):
        if adm_level == "0":
            return [{"label": "", "value": ""}], "", True
        adm = app.data.get("adm")
        adm_f = adm[adm["ADM0_PCODE"] == iso3_to_pcode.get(iso3)].sort_values(
            by="ADM1_NAME"
        )
        return (
            [
                {"label": name, "value": pcode}
                for (pcode, name) in adm_f.groupby("ADM1_PCODE")["ADM1_NAME"]
                .first()
                .items()
            ],
            adm_f["ADM1_PCODE"].iloc[0],
            False,
        )

    @app.callback(
        Output("adm2", "options"),
        Output("adm2", "value"),
        Output("adm2", "disabled"),
        Input("adm_level", "value"),
        Input("adm1", "value"),
    )
    def update_adm2_dropdown(adm_level, adm1):
        if adm_level in ["0", "1"]:
            return [{"label": "", "value": ""}], "", True
        adm = app.data.get("adm")
        adm_f = adm[adm["ADM1_PCODE"] == adm1].sort_values(by="ADM2_NAME")
        return (
            [
                {"label": name, "value": pcode}
                for (pcode, name) in adm_f.groupby("ADM2_PCODE")["ADM2_NAME"]
                .first()
                .items()
            ],
            adm_f["ADM2_PCODE"].iloc[0],
            False,
        )

    @app.callback(
        Output("timeseries", "figure"),
        Output("rp", "figure"),
        Input("adm_level", "value"),
        Input("iso3", "value"),
        Input("adm1", "value"),
        Input("adm2", "value"),
    )
    def update_timeseries_rp_plots(adm_level, iso3, adm1_pcode, adm2_pcode):
        # initial processing
        window = 7
        df = app.data.get(iso3).copy()
        adm = app.data.get("adm").copy()
        adm = adm[adm["ADM0_PCODE"] == iso3_to_pcode.get(iso3)]
        most_recent_date_str = f"{df['date'].max():%Y-%m-%d}"
        val_col = f"roll{window}"

        seasonal = (
            df[df["date"].dt.year < 2024]
            .groupby(["ADM1_PCODE", "ADM2_PCODE", "dayofyear"])[val_col]
            .mean()
            .reset_index()
        )
        seasonal["eff_date"] = pd.to_datetime(seasonal["dayofyear"], format="%j")
        today_dayofyear = df.iloc[-1]["dayofyear"]
        df_to_today = df[df["dayofyear"] <= today_dayofyear]

        df_past_month = df_to_today[df_to_today["dayofyear"] >= today_dayofyear - 30]
        up_to_today = True
        past_month_only = False

        df_for_peaks = df_to_today if up_to_today else df
        df_for_peaks = df_past_month if past_month_only else df_for_peaks

        peak_anytime = (
            df_for_peaks.groupby(
                [df_for_peaks["date"].dt.year, "ADM1_PCODE", "ADM2_PCODE"]
            )[val_col]
            .max()
            .reset_index()
        )

        # aggregation by admin
        if adm_level == "0":
            adm_name = adm.iloc[0]["ADM0_NAME"]
            dff = (
                df.groupby(["dayofyear", "date"])[val_col]
                .sum()
                .reset_index()
                .sort_values("date", ascending=False)
            )
            dff["eff_date"] = pd.to_datetime(dff["dayofyear"], format="%j")
            seasonal_f = seasonal.groupby("eff_date")[val_col].sum().reset_index()
            peak_anytime_f = peak_anytime.groupby("date")[val_col].sum().reset_index()
        elif adm_level == "1":
            adm_name = adm[adm["ADM1_PCODE"] == adm1_pcode].iloc[0]["ADM1_NAME"]
            dff = (
                df[df["ADM1_PCODE"] == adm1_pcode]
                .sort_values("date", ascending=False)
                .groupby(["dayofyear", "date"])[val_col]
                .sum()
                .reset_index()
                .sort_values("date", ascending=False)
            )
            dff["eff_date"] = pd.to_datetime(dff["dayofyear"], format="%j")
            seasonal_f = (
                seasonal[seasonal["ADM1_PCODE"] == adm1_pcode]
                .groupby("eff_date")[val_col]
                .sum()
                .reset_index()
            )
            peak_anytime_f = (
                peak_anytime[peak_anytime["ADM1_PCODE"] == adm1_pcode]
                .groupby("date")[val_col]
                .sum()
                .reset_index()
            )
        elif adm_level == "2":
            adm_name = adm[adm["ADM2_PCODE"] == adm2_pcode].iloc[0]["ADM2_NAME"]
            dff = df[df["ADM2_PCODE"] == adm2_pcode].sort_values(
                "date", ascending=False
            )
            seasonal_f = seasonal[seasonal["ADM2_PCODE"] == adm2_pcode]
            peak_anytime_f = peak_anytime[
                peak_anytime["ADM2_PCODE"] == adm2_pcode
            ].copy()
        else:
            raise ValueError("adm_level must be 0, 1, or 2")

        # rp calculation
        rp = 3

        peak_anytime_f["rank"] = peak_anytime_f[val_col].rank(ascending=False)
        peak_anytime_f["rp"] = len(peak_anytime_f) / peak_anytime_f["rank"]
        peak_anytime_f[f"{rp}yr_rp"] = peak_anytime_f["rp"] >= rp
        peak_years = peak_anytime_f[peak_anytime_f[f"{rp}yr_rp"]]["date"].to_list()

        # timeseries plot
        fig_timeseries = go.Figure()

        # seasonal
        fig_timeseries.add_trace(
            go.Scatter(
                x=seasonal_f["eff_date"],
                y=seasonal_f[val_col],
                name="Average",
                line_color="black",
                line_width=2,
            )
        )

        # past years
        for year in dff["date"].dt.year.unique():
            if year == 2024:
                color = CHD_GREEN
                linewidth = 3
            elif year in peak_years:
                color = "red"
                linewidth = 0.2
            else:
                color = "grey"
                linewidth = 0.2
            dff_year = dff[dff["date"].dt.year == year]
            fig_timeseries.add_trace(
                go.Scatter(
                    x=dff_year["eff_date"],
                    y=dff_year[val_col],
                    name=str(year),
                    line_color=color,
                    line_width=linewidth,
                )
            )

        fig_timeseries.update_layout(
            template="simple_white",
            xaxis=dict(tickformat="%b %d", dtick="M1"),
            title=f"{adm_name} - time series<br>"
            f"<sup>Years above 3-year return period shown in red</sup>",
            legend_title="Year",
            height=600,
            margin={"t": 50, "l": 0, "r": 0, "b": 0},
        )
        fig_timeseries.update_yaxes(
            rangemode="tozero", title="Population exposed to flooding"
        )
        fig_timeseries.update_xaxes(title="Date")

        # rp plot
        peak_anytime_f = peak_anytime_f.sort_values("rp")

        fig_rp = go.Figure()
        # all years
        fig_rp.add_trace(
            go.Scatter(
                x=peak_anytime_f["rp"],
                y=peak_anytime_f[val_col],
                name="all years",
                mode="lines",
                line_color="black",
            )
        )
        # 2024
        peak_2024 = peak_anytime_f.set_index("date").loc[2024]
        if peak_2024["rank"] == 1:
            position = "bottom left"
        elif peak_2024["rank"] == len(peak_anytime_f):
            position = "top right"
        else:
            position = "bottom right"

        fig_rp.add_trace(
            go.Scatter(
                x=[peak_2024["rp"]],
                y=[peak_2024[val_col]],
                text=f"2024:<br>Exposure = {int(peak_2024[val_col]):,} people<br>"
                f"Return period = {peak_2024['rp']:.1f} years",
                name="current year",
                textposition=position,
                mode="markers+text",
                marker_color=CHD_GREEN,
                textfont=dict(size=15, color=CHD_GREEN),
                marker_size=10,
            )
        )

        # other bad years
        rp_peaks = peak_anytime_f[
            (peak_anytime_f[f"{rp}yr_rp"]) & (peak_anytime_f["date"] != 2024)
        ]
        fig_rp.add_trace(
            go.Scatter(
                x=rp_peaks["rp"],
                y=rp_peaks[val_col],
                text=rp_peaks["date"],
                name="≥3-yr RP years",
                textposition="top left",
                mode="markers+text",
                marker_color="red",
                textfont=dict(size=12, color="red"),
                marker_size=5,
            )
        )

        fig_rp.update_layout(
            template="simple_white",
            xaxis=dict(dtick=1),
            height=600,
            title=f"{adm_name} - return period<br><sup>(as of {most_recent_date_str})</sup>",
            showlegend=False,
            margin={"t": 50, "l": 0, "r": 0, "b": 0},
        )
        fig_rp.update_yaxes(
            title="Total population exposed to flooding during the year"
        )
        fig_rp.update_xaxes(title="Return period (years)")

        return fig_timeseries, fig_rp
