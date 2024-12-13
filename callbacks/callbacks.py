import json

import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update
from dash_extensions.javascript import arrow_function, assign

from constants import ATTRIBUTION, URL, URL_LABELS
from utils.chart_utils import create_return_period_plot, create_timeseries_plot
from utils.data_utils import (
    calculate_return_periods,
    fetch_flood_data,
    get_summary,
    process_flood_data,
)
from utils.log_utils import get_logger

logger = get_logger("callbacks")

style_handle = assign(
    """
    function(feature, context) {
        const {colorscale, style, colorProp, selected} = context.hideout;  // get props from hideout
        const value = feature.properties[colorProp];  // get value that determines the color
        let featureStyle = {...style};

        // Only modify opacity if this feature's pcode matches selected
        if (selected === feature.properties.pcode) {
            featureStyle.fillOpacity = 1;
            featureStyle.color = "black";
            featureStyle.weight = 1;
        }

        // Set color based on value
        if (value === -1) {
            featureStyle.fillColor = colorscale[0];
        } else if (value === 0) {
            featureStyle.fillColor = colorscale[1];
        } else if (value === 1) {
            featureStyle.fillColor = colorscale[2];
        }

        return featureStyle;
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
        with open(f"assets/geo/adm{adm_level}.json", "r") as file:
            data = json.load(file)

        # TODO: Read from db
        df_tercile = pd.read_csv(f"temp/adm{adm_level}_terciles.csv")
        features_df = pd.DataFrame(
            [feature["properties"] for feature in data["features"]]
        )
        df_joined = features_df.merge(
            df_tercile[["pcode", "tercile"]], on="pcode", how="left"
        )
        for feature, tercile in zip(data["features"], df_joined["tercile"]):
            feature["properties"]["tercile"] = tercile

        # Create diverging color scale (blue to white to red)
        colorscale = [
            "#6baed6",  # Medium blue
            "#dbdbdb",
            "#fcae91",  # Light red
        ]

        colorbar = dlx.categorical_colorbar(
            categories=["Below average", "Average", "Above average"],
            colorscale=colorscale,
            width=300,
            height=15,
            position="bottomleft",
        )
        title = html.Div(
            "Population exposed to flooding is...",
            style={
                "position": "absolute",
                "bottom": "40px",
                "left": "10px",
                "zIndex": 1000,
                "fontSize": "12px",
                "paddingBottom": "5px",
                "fontWeight": "bold",
            },
        )

        style = dict(weight=1, opacity=1, color="white", fillOpacity=0.5)

        geojson = dl.GeoJSON(
            data=data,
            id="geojson",
            style=style_handle,
            hideout=dict(
                colorscale=colorscale,
                style=style,
                colorProp="tercile",
                selected="",
            ),
            hoverStyle=arrow_function(
                {"fillOpacity": 1, "weight": 1, "color": "black"}
            ),
            zoomToBounds=False,
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
            dl.Pane(
                dl.TileLayer(url=URL_LABELS, attribution=ATTRIBUTION),
                name="tile",
                style={"zIndex": 1002},
            ),
            title,
            colorbar,
        ]

    @app.callback(
        Output("exposure-chart", "children"),
        Output("rp-chart", "children"),
        Output("place-name", "children"),
        Output("num-exposed", "children"),
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
            return (
                blank_children,
                blank_children,
                dmc.Center("No location selected"),
                "",
            )
        df_exposure, df_adm = fetch_flood_data(pcode, adm_level)

        if len(df_exposure) == 0:
            logger.warning(f"No data available for {pcode}")
            empty_children = [
                dmc.Space(h=100),
                dmc.Center(
                    html.Div("No data available for selected location")
                ),
            ]
            return (
                empty_children,
                empty_children,
                dmc.Center("No data available"),
                "",
            )

        # Process data
        df_processed, df_seasonal, df_peaks = process_flood_data(df_exposure)
        df_peaks, peak_years = calculate_return_periods(df_peaks)

        # Create plots
        fig_timeseries = create_timeseries_plot(
            df_seasonal, df_processed, peak_years
        )
        fig_rp = create_return_period_plot(df_peaks)

        exposure_chart = dcc.Graph(
            config={"displayModeBar": False}, figure=fig_timeseries
        )
        rp_chart = dcc.Graph(config={"displayModeBar": False}, figure=fig_rp)
        name, exposed_summary = get_summary(df_processed, df_adm, adm_level)
        return exposure_chart, rp_chart, name, exposed_summary
