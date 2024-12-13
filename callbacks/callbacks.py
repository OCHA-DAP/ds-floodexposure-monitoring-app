import json

import dash_leaflet as dl
import dash_leaflet.express as dlx
import dash_mantine_components as dmc
import jenkspy
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
        const {classes, colorscale, style, colorProp, selected} = context.hideout;  // get props from hideout

        const value = feature.properties[colorProp];  // get value the determines the color
        for (let i = 0; i < classes.length; ++i) {
            if (value > classes[i]) {
                style.fillColor = colorscale[i];  // set the fill color according to the class
            }
        }
        return style;

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
        df_anomaly = pd.read_csv(f"temp/adm{adm_level}_anomaly.csv")
        features_df = pd.DataFrame(
            [feature["properties"] for feature in data["features"]]
        )
        df_joined = features_df.merge(
            df_anomaly[["pcode", "anomaly"]], on="pcode", how="left"
        )
        for feature, anomaly in zip(data["features"], df_joined["anomaly"]):
            feature["properties"]["anomaly"] = anomaly

        # Split data into negative and positive values
        neg_values = df_joined["anomaly"][df_joined["anomaly"] < 0].values
        pos_values = df_joined["anomaly"][df_joined["anomaly"] >= 0].values

        # Compute breaks for negative and positive values separately
        if len(neg_values) > 0:
            neg_breaks = jenkspy.jenks_breaks(
                abs(neg_values), n_classes=2
            )  # 3 classes for negative
            neg_breaks = [
                -x for x in reversed(neg_breaks)
            ]  # Reverse and make negative
        else:
            neg_breaks = [0]  # If no negative values

        if len(pos_values) > 0:
            pos_breaks = jenkspy.jenks_breaks(
                pos_values, n_classes=2
            )  # 3 classes for positive
        else:
            pos_breaks = [0]  # If no positive values

        # Combine breaks, ensuring zero is included
        classes = sorted(list(set(neg_breaks + [0] + pos_breaks)))

        # Create diverging color scale (blue to white to red)
        colorscale = [
            "#3182bd",  # Dark blue
            "#6baed6",  # Medium blue
            "#dbdbdb",  # Light blue
            "#fcae91",  # Light red
            "#fb6a4a",  # Medium red
        ]

        # Format the break points for display
        ctg = []
        for idx, _ in enumerate(classes[:-1]):
            print(classes[idx])
            if classes[idx + 1] == 0:
                ctg.append(0)
            else:
                ctg.append(
                    f"{int(classes[idx]):,} to {int(classes[idx+1]):,}"
                )  # noqa

        colorbar = dlx.categorical_colorbar(
            categories=ctg,
            colorscale=colorscale,
            width=500,
            height=15,
            position="bottomleft",
        )

        style = dict(weight=1, opacity=1, color="white", fillOpacity=1)

        geojson = dl.GeoJSON(
            data=data,
            id="geojson",
            style=style_handle,
            hideout=dict(
                colorscale=colorscale,
                classes=classes,
                style=style,
                colorProp="anomaly",
                selected="",
            ),
            hoverStyle=arrow_function({"fillOpacity": 1}),
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
            dl.Pane(
                dl.TileLayer(url=URL_LABELS, attribution=ATTRIBUTION),
                name="tile",
                style={"zIndex": 1002},
            ),
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

    # TODO: Would be better as a clientside callback, but couldn't seem to get it to work...
    @app.callback(
        Output("hover-place-name", "children"), Input("geojson", "hoverData")
    )
    def info_hover(feature):
        if feature:
            return round(feature["properties"]["anomaly"])
