import json
from urllib.parse import parse_qs

import dash_leaflet as dl
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update
from dash_extensions.javascript import arrow_function, assign

from constants import (
    ATTRIBUTION,
    CHD_BLUE,
    CHD_LIGHTBLUE,
    COLORSCALE,
    HEATMAP_ZOOM_THRESHOLD,
    OCHA_BLUE,
    URL,
    URL_LABELS,
)
from utils.chart_utils import create_timeseries_plot
from utils.data_utils import (
    calculate_return_periods,
    fetch_flood_data,
    get_current_quantiles,
    get_summary,
    process_flood_data,
)
from utils.log_utils import get_logger

logger = get_logger("callbacks")


def pcode_from_search(search):
    """Extract the selected pcode from a URL query string, if present."""
    params = parse_qs((search or "").lstrip("?"))
    return params.get("pcode", [""])[0]


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

LOCATIONS_PANE = "locations"

# dash-leaflet has no built-in heatmap component, so this loads the
# Leaflet.heat plugin (which registers itself on the global `L`) on
# demand and builds the layer by hand once the wrapping LayerGroup
# mounts. The plugin is loaded here - rather than via Dash's
# external_scripts, which inject <script> tags into <head> with no
# guaranteed ordering against dash-leaflet's own bundle - so it can't
# race `window.L` being defined. Leaflet.heat always renders into
# Leaflet's built-in overlayPane rather than a custom `pane` option,
# so that pane's z-index is bumped here to sit above our
# admin/choropleth panes (which otherwise top out at 1000) instead of
# adding a second competing "locations" pane concept.
heat_layer_handler = assign(
    """
    function(e, ctx) {
        const layerGroup = e.target;
        const map = layerGroup._map;
        const overlayPane = map.getPane("overlayPane");
        if (overlayPane) overlayPane.style.zIndex = 1001;

        function buildHeatLayer() {
            window.getLocationsData()
                .then((features) => {
                    const points = features.map(
                        (f) => [f.geometry.coordinates[1], f.geometry.coordinates[0]]
                    );
                    const heat = L.heatLayer(points, {
                        radius: 10,
                        blur: 3,
                        maxZoom: 12,
                        minOpacity: 0.1,
                        gradient: {0.3: "%s", 0.6: "%s", 1.0: "%s"},
                    });
                    layerGroup.addLayer(heat);
                    window._heatLayer = heat;

                    // The heat canvas otherwise always renders visible
                    // once built - fetching+building it is async, so
                    // it can finish well after the toggle callback's
                    // one relevant firing already ran (and found no
                    // canvas yet to hide). Reading the checkbox's live
                    // DOM state here, at the moment the canvas is
                    // actually created, is what makes an unchecked
                    // default reliably stay hidden regardless of that
                    // timing.
                    const toggle = document.getElementById(
                        "locations-toggle"
                    );
                    if (toggle && !toggle.checked) {
                        heat._canvas.style.display = "none";
                    }
                })
                .catch((err) => console.error("Heatmap layer failed:", err));
        }

        if (typeof L.heatLayer === "function") {
            buildHeatLayer();
        } else {
            const script = document.createElement("script");
            script.src = "https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js";
            script.onload = buildHeatLayer;
            script.onerror = () => console.error("Failed to load leaflet.heat plugin");
            document.head.appendChild(script);
        }
    }
"""
    % (CHD_LIGHTBLUE, CHD_BLUE, OCHA_BLUE)
)

# Individual-points counterpart to the heat layer above, shown instead
# of the heatmap once zoomed in past HEATMAP_ZOOM_THRESHOLD (see the
# toggle clientside_callback in register_callbacks). Only ever holds
# markers for whatever's in the current viewport - never all ~12k
# points at once - via window.rebuildPointsLayer (assets/heatmap.js),
# which is what actually populates window._pointsLayer on demand. This
# handler just sets up the (initially empty) layer once, when its
# wrapping LayerGroup mounts. The point color is threaded in from
# OCHA_BLUE the same way the heat layer's gradient colors are above,
# rather than hardcoding a second copy in the static heatmap.js file.
points_layer_handler = assign(
    """
    function(e, ctx) {
        const layerGroup = e.target;
        const points = L.layerGroup();
        layerGroup.addLayer(points);
        window._pointsLayer = points;
        window.LOCATIONS_POINT_COLOR = "%s";
    }
"""
    % OCHA_BLUE
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

    # Below HEATMAP_ZOOM_THRESHOLD, the heat layer is shown (as before).
    # At/above it, individual points are shown instead, rebuilt for
    # just the current viewport from the cached fetch (see
    # window.rebuildPointsLayer in assets/heatmap.js) rather than ever
    # rendering all ~12k points at once. Both layers are always
    # mounted - "showing"/"hiding" the heat layer is a CSS toggle on
    # its one canvas element, and "hiding" the points layer is just
    # clearing its (viewport-scoped, so already small) marker set.
    #
    # prevent_initial_call is deliberately NOT set here: the toggle
    # defaults to unchecked, and without an initial firing nothing
    # would ever apply that - the heat canvas would render visible on
    # load regardless, since there's no other code path that hides it.
    # checked=False short-circuits both showHeat/showPoints to false
    # even if zoom/bounds haven't populated yet on this first call, so
    # firing before the layers exist is harmless either way.
    app.clientside_callback(
        """
        function(checked, zoom, bounds) {
            const threshold = %s;
            const heat = window._heatLayer;
            const showHeat = checked && zoom < threshold;
            if (heat && heat._canvas) heat._canvas.style.display = showHeat ? "" : "none";

            const showPoints = checked && zoom >= threshold;
            if (showPoints && bounds) {
                window.rebuildPointsLayer(bounds);
            } else if (window._pointsLayer) {
                window._pointsLayer.clearLayers();
            }
            return "";
        }
        """
        % HEATMAP_ZOOM_THRESHOLD,
        Output("heatmap-visibility-dummy", "children"),
        Input("locations-toggle", "checked"),
        Input("map", "zoom"),
        Input("map", "bounds"),
    )

    @app.callback(
        Output("map", "children"),
        Input("adm-level", "value"),
        State("selected-data", "data"),
        State("url", "search"),
    )
    def set_adm_value(adm_level, selected_data, search):
        # Prefer the live selection; on a fresh load from a shared link
        # selected-data is still empty, so fall back to the URL pcode.
        selected_pcode = (
            selected_data.get("pcode", "")
            if selected_data
            else pcode_from_search(search)
        )
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

        style = dict(weight=1, opacity=1, color="white", fillOpacity=0.75)

        geojson = dl.GeoJSON(
            data=data,
            id="geojson",
            style=style_handle,
            hideout=dict(
                colorscale=COLORSCALE,
                style=style,
                colorProp="quantile",
                selected=selected_pcode,
            ),
            hoverStyle=arrow_function({"weight": 2, "color": "#666666"}),
            zoomToBounds=False,
        )
        adm0 = dl.GeoJSON(
            url="assets/geo/adm0_outline.json",
            id="adm0-geojson",
            style={"color": "#353535", "weight": 1.5},
        )

        # Both the heat layer and the points layer are always mounted -
        # nothing here adds/removes them; the toggle/zoom
        # clientside_callback above controls what's actually visible
        # in each. That's simpler and more reliable than trying to
        # add/remove the underlying Leaflet layers through
        # dash-leaflet's React lifecycle on every toggle or zoom.
        locations_children = [
            dl.LayerGroup(
                id="locations-heat",
                eventHandlers=dict(add=heat_layer_handler),
            ),
            dl.LayerGroup(
                id="locations-points",
                eventHandlers=dict(add=points_layer_handler),
            ),
        ]

        return [
            dl.TileLayer(url=URL, attribution=ATTRIBUTION),
            dl.Pane(adm0, style={"zIndex": 1001}, name="adm0"),
            dl.Pane(geojson, style={"zIndex": 1000}, name="sel"),
            dl.Pane(
                locations_children,
                style={"zIndex": 1001},
                name=LOCATIONS_PANE,
            ),
            dl.Pane(
                dl.TileLayer(url=URL_LABELS, attribution=ATTRIBUTION),
                name="tile",
                style={"zIndex": 1002},
            ),
        ]

    @app.callback(
        Output("exposure-chart", "children"),
        Output("place-name", "children"),
        Output("num-exposed", "children"),
        Output("exposure-chart-title", "children"),
        Input("selected-data", "data"),
        State("adm-level", "value"),
        prevent_initial_call=False,
    )
    def update_plot(selected_data, adm_level):
        exposed_plot_title = "Daily population exposed to flooding"

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
                dmc.Center("No location selected"),
                "",
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
                dmc.Center("No data available"),
                "",
                no_update,
            )

        # Process data
        df_processed, df_seasonal, df_peaks = process_flood_data(df_exposure)
        df_peaks, peak_years = calculate_return_periods(df_peaks)

        # Create plot
        fig_timeseries = create_timeseries_plot(
            df_seasonal, df_processed, peak_years
        )

        exposure_chart = dcc.Graph(
            config={"displayModeBar": False}, figure=fig_timeseries
        )
        name, exposed_summary = get_summary(
            df_processed, df_adm, adm_level, quantile
        )
        return (
            exposure_chart,
            name,
            exposed_summary,
            f"{exposed_plot_title}: {name}",
        )

    @app.callback(
        Output("hover-place-name", "children"), Input("geojson", "hoverData")
    )
    def info_hover(feature):
        if feature:
            return feature["properties"]["name"]

    @app.callback(
        Output("url", "search"),
        Input("selected-data", "data"),
        State("adm-level", "value"),
        prevent_initial_call=True,
    )
    def update_url(selected_data, adm_level):
        """Persist the current selection to the URL query string so the
        view can be shared and restored."""
        if not selected_data or not selected_data.get("pcode"):
            return ""
        return f"?adm={adm_level}&pcode={selected_data['pcode']}"

    @app.callback(
        Output("adm-level", "value"),
        Output("selected-data", "data", allow_duplicate=True),
        Input("url", "search"),
        State("selected-data", "data"),
        prevent_initial_call="initial_duplicate",
    )
    def restore_from_url(search, current_data):
        """On load (or when the query string changes), restore the admin
        level and selected pcode encoded in the URL."""
        params = parse_qs((search or "").lstrip("?"))
        pcode = params.get("pcode", [""])[0]
        adm_level = params.get("adm", [None])[0]

        if not pcode:
            return no_update, no_update

        # Break the write -> read feedback loop: if the URL already
        # matches the current selection, there is nothing to restore.
        if current_data and current_data.get("pcode") == pcode:
            return no_update, no_update

        adm_out = adm_level if adm_level in ("0", "1", "2") else no_update

        # Look up the quantile for the pcode so the summary can render.
        df_quantile = get_current_quantiles(adm_level)
        row = df_quantile[df_quantile["pcode"] == pcode]
        if row.empty or pd.isna(row.iloc[0]["quantile"]):
            return adm_out, no_update

        quantile = int(row.iloc[0]["quantile"])
        return adm_out, {"pcode": pcode, "quantile": quantile}
