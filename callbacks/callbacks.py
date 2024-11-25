import dash_leaflet as dl
import dash_mantine_components as dmc
from dash import Input, Output, State, dcc, html, no_update
from dash_extensions.javascript import arrow_function, assign

# TODO: Be more careful with engine?
from constants import ATTRIBUTION, CHD_GREEN, URL, URL_LABELS, engine
from utils.chart_utils import create_return_period_plot, create_timeseries_plot
from utils.data_utils import (calculate_return_periods, fetch_flood_data,
                              get_summary, process_flood_data)
from utils.log_utils import get_logger

logger = get_logger("callbacks")

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
            dl.Pane(
                dl.TileLayer(url=URL_LABELS, attribution=ATTRIBUTION),
                name="tile",
                style={"zIndex": 1002},
            ),
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
        df_exposure, df_adm = fetch_flood_data(engine, pcode, adm_level)

        if len(df_exposure) == 0:
            logger.warning(f"No data available for {pcode}")
            return (
                [
                    dmc.Space(h=100),
                    dmc.Center(html.Div("No data available for selected location")),
                ],
                dmc.Center("No data available"),
                "",
            )

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
        name, exposed_summary = get_summary(df_exposure, df_adm, adm_level)
        return exposure_chart, rp_chart, name, exposed_summary

    # TODO: Would be better as a clientside callback, but couldn't seem to get it to work...
    @app.callback(Output("hover-place-name", "children"), Input("geojson", "hoverData"))
    def info_hover(feature):
        if feature:
            return feature["properties"]["name"]
