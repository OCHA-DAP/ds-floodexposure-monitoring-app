import time

import dash_leaflet as dl
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update
from dash_extensions.javascript import arrow_function, assign
from sqlalchemy import text

# TODO: Be more careful with engine?
from constants import ATTRIBUTION, CHD_GREEN, URL, engine
from utils.chart_utils import create_return_period_plot, create_timeseries_plot
from utils.data_utils import (calculate_return_periods, fetch_flood_data,
                              process_flood_data)

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
        Output("exposure-chart", "children"),
        Output("rp-chart", "children"),
        Input("selected-pcode", "data"),
        State("adm-level", "value"),
        prevent_initial_call=False,
    )
    def update_plot(pcode, adm_level):
        if not pcode:
            blank_children = [
                dmc.Space(h=100),
                dmc.Center(html.Div("Select a location from the map above")),
            ]
            return blank_children, blank_children

        # Fetch data
        start = time.time()
        df_exposure, df_adm = fetch_flood_data(engine, pcode, adm_level)

        if len(df_exposure) == 0:
            return [
                dmc.Space(h=100),
                dmc.Center(html.Div("No data available for selected location")),
            ]

        # Process data
        df_processed, df_seasonal, df_peaks = process_flood_data(
            df_exposure, pcode, adm_level
        )
        df_peaks, peak_years = calculate_return_periods(df_peaks)

        # Create plots
        fig_timeseries = create_timeseries_plot(
            df_seasonal, df_processed, peak_years, CHD_GREEN
        )
        fig_rp = create_return_period_plot(df_peaks, CHD_GREEN)

        exposure_chart = dcc.Graph(
            config={"displayModeBar": False}, figure=fig_timeseries
        )
        rp_chart = dcc.Graph(config={"displayModeBar": False}, figure=fig_rp)

        return exposure_chart, rp_chart

    @app.callback(
        Output("place-name", "children"),
        Output("num-exposed", "children"),
        Input("selected-pcode", "data"),
        State("adm-level", "value"),
        prevent_initial_call=False,
    )
    def update_info(pcode, adm_level):
        if not pcode:
            return dmc.Center("No location selected"), ""
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
        )
