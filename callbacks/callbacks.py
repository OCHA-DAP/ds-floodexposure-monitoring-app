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
    get_current_quantiles,
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
        if (value === -2) {
            featureStyle.fillColor = colorscale[0];
        } else if (value === -1) {
            featureStyle.fillColor = colorscale[1];
        } else if (value === 0) {
            featureStyle.fillColor = colorscale[2];
        } else if (value === 1) {
            featureStyle.fillColor = colorscale[3];
        } else if (value === 2) {
            featureStyle.fillColor = colorscale[4];
        }

        return featureStyle;
    }
"""
)


def register_callbacks(app):
    @app.callback(
        Output("selected-data", "data"),
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
        return feature["properties"], hideout

    @app.callback(Output("map", "children"), Input("adm-level", "value"))
    def set_adm_value(adm_level):
        with open(f"assets/geo/adm{adm_level}.json", "r") as file:
            data = json.load(file)

        df_quantile = get_current_quantiles(adm_level)
        features_df = pd.DataFrame(
            [feature["properties"] for feature in data["features"]]
        )
        df_joined = features_df.merge(
            df_quantile[["pcode", "quantile"]], on="pcode", how="left"
        )
        for feature, quantile in zip(data["features"], df_joined["quantile"]):
            feature["properties"]["quantile"] = quantile

        colorscale = ["#0063b3", "#66b0ec", "#cccccc", "#fce0de", "#f2645a"]
        colorbar = dlx.categorical_colorbar(
            categories=[
                "Well below<br>normal",
                "Below normal",
                "Normal",
                "Above normal",
                "Well above<br>normal",
            ],
            colorscale=colorscale,
            width=300,
            height=15,
            position="bottomleft",
        )
        title = html.Div(
            "Population exposed to flooding is...",
            style={
                "position": "absolute",
                "bottom": "60px",
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
                colorProp="quantile",
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
            style={"color": "#353535", "weight": 1.5},
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
        Output("exposure-chart-title", "children"),
        Output("rp-chart-title", "children"),
        Input("selected-data", "data"),
        State("adm-level", "value"),
        prevent_initial_call=False,
    )
    def update_plot(selected_data, adm_level):
        exposed_plot_title = "Daily population exposed to flooding"
        rp_plot_title = "Return period of annual maximum flood exposure"

        if not selected_data:
            blank_children = [
                dmc.Space(h=100),
                dmc.Center(
                    html.Div(
                        "Select a location from the map above",
                        style={"color": "#888888"},
                    )
                ),
            ]
            return (
                blank_children,
                blank_children,
                dmc.Center("No location selected"),
                "",
                no_update,
                no_update,
            )

        pcode = selected_data["pcode"]
        quantile = selected_data["quantile"]

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
        name, exposed_summary = get_summary(
            df_processed, df_adm, adm_level, quantile
        )
        return (
            exposure_chart,
            rp_chart,
            name,
            exposed_summary,
            f"{exposed_plot_title}: {name}",
            f"{rp_plot_title}: {name}",
        )

    @app.callback(
        Output("hover-place-name", "children"), Input("geojson", "hoverData")
    )
    def info_hover(feature):
        if feature:
            return feature["properties"]["name"]
