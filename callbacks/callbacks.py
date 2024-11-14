import time

import dash_leaflet as dl
import dash_mantine_components as dmc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html, no_update
from dash_extensions.javascript import arrow_function, assign
from sqlalchemy import text

from constants import ATTRIBUTION, CHD_GREEN, URL, engine, pcode_to_iso3

style_handle = assign(
    """
    function(feature, context) {
        const selected = context.hideout.selected

        if(selected.includes(feature.properties.pcode)){
            return {
                fillColor: '#1f77b4',
                weight: 0.8,
                opacity: 1,
                color: 'white',
                fillOpacity: 0.8
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

        name = feature["properties"]["pcode"]
        if hideout["selected"] == name:
            hideout["selected"] = ""
        else:
            hideout["selected"] = name
        return name, hideout

    @app.callback(Output("map", "children"), Input("adm-level", "value"))
    def set_adm_value(adm_level):
        geojson = dl.GeoJSON(
            url=f"assets/geo/adm{adm_level}.json",
            id="geojson",
            style=style_handle,
            hideout=dict(selected=""),
            hoverStyle=arrow_function({"fillColor": "#1f77b4", "fillOpacity": 0.8}),
            zoomToBounds=True,
        )
        adm0 = dl.GeoJSON(
            url="assets/geo/adm0_outline.json",
            id="adm0-geojson",
            style={"color": "black", "weight": 3},
        )

        return [
            dl.TileLayer(url=URL, attribution=ATTRIBUTION),
            dl.Pane(adm0, style={"zIndex": 1001}, name="adm0"),
            dl.Pane(geojson, style={"zIndex": 1000}, name="sel"),
        ]

    @app.callback(
        Output("figure-div", "children"),
        Input("selected-pcode", "data"),
        State("adm-level", "value"),
        prevent_initial_call=False,
    )
    def update_timeseries_plot(pcode, adm_level):
        if not pcode:
            return [
                dmc.Space(h=100),
                dmc.Center(html.Div("Select a location from the map above")),
            ]
        iso3 = pcode_to_iso3.get(pcode[:2])
        start = time.time()
        print(f"Getting data for {iso3}...")
        query_exposure = text(
            f"select * from app.flood_exposure where adm{adm_level}_pcode=:pcode"
        )
        query_adm = text("select * from app.adm")
        with engine.connect() as con:
            df = pd.read_sql_query(query_exposure, con, params={"pcode": pcode})
            adm = pd.read_sql_query(query_adm, con)
            adm = adm[adm[f"adm{adm_level}_pcode"] == pcode]

        adm_name = adm.iloc[0][f"adm{adm_level}_name"]
        elapsed = time.time() - start
        print(f"Data retrieved in {elapsed: .4f} seconds")
        print(f"{len(df)} rows of flood exposure data for {adm_name}")
        if len(df) == 0:
            return [
                dmc.Space(h=100),
                dmc.Center(html.Div("No data available for selected location")),
            ]
        start = time.time()

        # initial processing
        window = 7
        val_col = f"roll{window}"

        seasonal = (
            df[df["date"].dt.year < 2024]
            .groupby(["adm1_pcode", "adm2_pcode", "dayofyear"])[val_col]
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
                [df_for_peaks["date"].dt.year, "adm1_pcode", "adm2_pcode"]
            )[val_col]
            .max()
            .reset_index()
        )

        # aggregation by admin
        if adm_level == "0":
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
            dff = (
                df[df["adm1_pcode"] == pcode]
                .sort_values("date", ascending=False)
                .groupby(["dayofyear", "date"])[val_col]
                .sum()
                .reset_index()
                .sort_values("date", ascending=False)
            )
            dff["eff_date"] = pd.to_datetime(dff["dayofyear"], format="%j")
            seasonal_f = (
                seasonal[seasonal["adm1_pcode"] == pcode]
                .groupby("eff_date")[val_col]
                .sum()
                .reset_index()
            )
            peak_anytime_f = (
                peak_anytime[peak_anytime["adm1_pcode"] == pcode]
                .groupby("date")[val_col]
                .sum()
                .reset_index()
            )
        elif adm_level == "2":
            dff = df[df["adm2_pcode"] == pcode].sort_values("date", ascending=False)
            seasonal_f = seasonal[seasonal["adm2_pcode"] == pcode]
            peak_anytime_f = peak_anytime[peak_anytime["adm2_pcode"] == pcode].copy()
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
            legend_title="Year<br><sup>(click to toggle)</sup>",
            height=265,
            margin={"t": 10, "l": 0, "r": 0, "b": 0},
            font=dict(family="Arial, sans-serif"),
        ),
        fig_timeseries.update_yaxes(
            rangemode="tozero", title="Population exposed to flooding"
        )
        fig_timeseries.update_xaxes(title="Date")

        elapsed = time.time() - start
        print(f"Processed data and made plots in {elapsed:.4f} seconds")
        return dcc.Graph(
            id="timeseries", config={"displayModeBar": False}, figure=fig_timeseries
        )

    @app.callback(
        Output("place-name", "children"),
        Output("num-exposed", "children"),
        Output("return-period", "children"),
        Input("selected-pcode", "data"),
        State("adm-level", "value"),
        prevent_initial_call=False,
    )
    def update_info(pcode, adm_level):
        if not pcode:
            return dmc.Center("No location selected"), "", ""
        query_exposure = text(
            f"select * from app.flood_exposure where adm{adm_level}_pcode=:pcode and date=(select max(date) from app.flood_exposure where adm{adm_level}_pcode=:pcode)"
        )
        query_adm = text(f"select * from app.adm where adm{adm_level}_pcode=:pcode")
        with engine.connect() as con:
            df = pd.read_sql_query(query_exposure, con, params={"pcode": pcode})
            adm = pd.read_sql_query(query_adm, con, params={"pcode": pcode})

        if len(df) == 0:
            return dmc.Center("No data available"), "", ""

        max_date = df.iloc[0]["date"].strftime("%Y-%m-%d")
        people_exposed = int(
            df.groupby([f"adm{adm_level}_pcode"])["roll7"]
            .sum()
            .reset_index()
            .iloc[0]["roll7"]
        )
        people_exposed_formatted = "{:,}".format(people_exposed)
        name = adm.iloc[0][f"adm{adm_level}_name"]
        return (
            name,
            f"{people_exposed_formatted} people exposed to flooding as of {max_date}.",
            "This is a X year return-period event.",
        )
