import time

import dash_leaflet as dl
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, no_update
from dash_extensions.javascript import arrow_function, assign
from sqlalchemy import text

from constants import ATTRIBUTION, CHD_GREEN, URL, engine, pcode_to_iso3

style_handle = assign(
    """
    function(feature, context) {
        const selected = context.hideout.selected

        if(selected.includes(feature.properties.ADM2_PCODE)){
            return {
                fillColor: '#1f77b4',
                weight: 0.8,
                opacity: 1,
                color: 'white',
                fillOpacity: 0.5
            }
        }
        return {
            fillColor: '#1f77b4',
            weight: 0.8,
            opacity: 1,
            color: 'white',
            fillOpacity: 0.3
        }
    }
"""
)


def register_callbacks(app):
    @app.callback(
        Output("selected-pcode", "data"),
        Output("geojson", "hideout"),
        Input("geojson", "n_clicks"),
        State("adm-level", "value"),
        State("geojson", "clickData"),
        State("geojson", "hideout"),
        prevent_initial_call=True,
    )
    def toggle_select(_, adm_level, feature, hideout):
        if not _:
            return no_update
        if not feature:
            return no_update

        name = feature["properties"][f"ADM{adm_level}_PCODE"]
        if hideout["selected"] == name:
            hideout["selected"] = ""
        else:
            hideout["selected"] = name
        return name, hideout

    # @app.callback(
    #     Output("selected-iso3", "data"),
    #     Output("geojson-adm0", "hideout"),
    #     Input("geojson-adm0", "n_clicks"),
    #     State("geojson-adm0", "clickData"),
    #     State("geojson-adm0", "hideout"),
    #     prevent_initial_call=True,
    # )
    # def toggle_select_adm0(_, feature, hideout):
    #     if not feature:
    #         return no_update
    #     name = feature["properties"]["iso_3"]
    #     if hideout["selected"] == name:
    #         hideout["selected"] = ""
    #     else:
    #         hideout["selected"] = name
    #     print(name)
    #     print(hideout)
    #     return name, hideout

    @app.callback(
        Output("hover-info", "children"),
        Input("selected-pcode", "data"),
    )
    def show_selection(sel_pcode):
        print("--")
        print(sel_pcode)
        return f"{sel_pcode}"

    @app.callback(Output("map", "children"), Input("adm-level", "value"))
    def set_adm_value(adm_level):
        geojson = dl.GeoJSON(
            url=f"assets/geo/bfa_adm{adm_level}.json",
            id="geojson",
            style=style_handle,
            hideout=dict(selected="BF5201"),
            hoverStyle=arrow_function(dict(weight=3, color="#666", dashArray="")),
            zoomToBounds=True,
        )

        # geojson_adm0 = dl.GeoJSON(
        #     url="assets/geo/africa_adm0.json",
        #     id="geojson-adm0",
        #     style=adm0_style_handle,
        #     hideout=dict(selected=""),
        #     hoverStyle=arrow_function(dict(weight=2, color="#666", dashArray="")),
        #     zoomToBounds=False,
        # )
        return [dl.TileLayer(url=URL, attribution=ATTRIBUTION), geojson]

    @app.callback(
        Output("figure-div", "children"),
        Input("selected-pcode", "data"),
        State("adm-level", "value"),
        prevent_initial_call=False,
    )
    def update_timeseries_plot(pcode, adm_level):
        if not pcode:
            return dmc.Center(dmc.Text("Select an admin region from the map"))
        iso3 = pcode_to_iso3.get(pcode[:2])
        start = time.time()
        print(f"Getting data for {iso3}...")
        query_exposure = text("select * from app.flood_exposure where iso3=:iso3")
        query_adm = text("select * from app.adm")
        with engine.connect() as con:
            df = pd.read_sql_query(query_exposure, con, params={"iso3": iso3})
            adm = pd.read_sql_query(query_adm, con)
            # TODO Get query working on db
            # adm = adm[adm["ADM0_PCODE"] == pcode]

            print(pcode)

        elapsed = time.time() - start
        print(f"Data retrieved in {elapsed: .4f} seconds")
        print(f"{len(df)} rows of flood exposure data")
        start = time.time()

        # initial processing
        window = 7
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
            print("---")
            print(adm)
            print(pcode)
            adm_name = adm[adm["ADM1_PCODE"] == pcode].iloc[0]["ADM1_NAME"]
            dff = (
                df[df["ADM1_PCODE"] == pcode]
                .sort_values("date", ascending=False)
                .groupby(["dayofyear", "date"])[val_col]
                .sum()
                .reset_index()
                .sort_values("date", ascending=False)
            )
            dff["eff_date"] = pd.to_datetime(dff["dayofyear"], format="%j")
            seasonal_f = (
                seasonal[seasonal["ADM1_PCODE"] == pcode]
                .groupby("eff_date")[val_col]
                .sum()
                .reset_index()
            )
            peak_anytime_f = (
                peak_anytime[peak_anytime["ADM1_PCODE"] == pcode]
                .groupby("date")[val_col]
                .sum()
                .reset_index()
            )
        elif adm_level == "2":
            adm_name = adm[adm["ADM2_PCODE"] == pcode].iloc[0]["ADM2_NAME"]
            dff = df[df["ADM2_PCODE"] == pcode].sort_values("date", ascending=False)
            seasonal_f = seasonal[seasonal["ADM2_PCODE"] == pcode]
            peak_anytime_f = peak_anytime[peak_anytime["ADM2_PCODE"] == pcode].copy()
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
            legend_title="Year<br><sup>(click to toggle)</sup>",
            height=600,
            margin={"t": 50, "l": 0, "r": 0, "b": 0},
        )
        fig_timeseries.update_yaxes(
            rangemode="tozero", title="Population exposed to flooding"
        )
        fig_timeseries.update_xaxes(title="Date")

        elapsed = time.time() - start
        print(f"Processed data and made plots in {elapsed:.4f} seconds")
        return dcc.Graph(
            id="timeseries", config={"displayModeBar": False}, figure=fig_timeseries
        )
