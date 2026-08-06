import json
from urllib.parse import parse_qs

import dash_leaflet as dl
import dash_mantine_components as dmc
import pandas as pd
from dash import Input, Output, State, dcc, html, no_update
from dash_extensions.javascript import arrow_function, assign

from constants import (
    ATTRIBUTION,
    COLORSCALE,
    OCHA_BLUE,
    SITE_TYPES,
    URL,
    URL_LABELS,
    site_type_id,
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

# Only ever holds markers for whatever's in the current viewport - never
# all ~12k points at once - via window.rebuildPointsLayer
# (assets/heatmap.js), which is what actually populates
# window._pointsLayer on demand. This handler just sets up the
# (initially empty) layer once, when its wrapping LayerGroup mounts.
# The point color is threaded in from OCHA_BLUE the same way other
# Python-sourced constants are, rather than hardcoding a second copy in
# the static heatmap.js file. attachPointsHoverTooltip (also in
# heatmap.js) is idempotent - safe to call on every mount even though
# it only actually wires up once.
points_layer_handler = assign(
    """
    function(e, ctx) {
        const layerGroup = e.target;
        const points = L.layerGroup();
        layerGroup.addLayer(points);
        window._pointsLayer = points;
        window.LOCATIONS_POINT_COLOR = "%s";
        window.attachPointsHoverTooltip(layerGroup._map);
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

    # Points are always rebuilt for just the current viewport (see
    # window.rebuildPointsLayer in assets/heatmap.js) rather than ever
    # rendering all ~12k at once - filtered both by bounds and by
    # whichever site types are checked below. There's no separate
    # master on/off control: if none are checked, allowedTypes ends up
    # empty and rebuildPointsLayer naturally renders nothing.
    #
    # prevent_initial_call is deliberately NOT set here: Village
    # defaults unchecked, and without an initial firing nothing would
    # apply that filter - rebuildPointsLayer would show every type on
    # first load regardless, since there's no other code path that
    # restricts it. Firing before window._pointsLayer exists yet is
    # harmless either way (rebuildPointsLayer no-ops if it's unset).
    app.clientside_callback(
        """
        function(bounds, ...typeChecked) {
            const siteTypes = [%s];
            const allowedTypes = siteTypes.filter((_, i) => typeChecked[i]);

            if (bounds) {
                window.rebuildPointsLayer(bounds, allowedTypes);
            } else if (window._pointsLayer) {
                window._pointsLayer.clearLayers();
            }
            return "";
        }
        """
        % ", ".join(f'"{site_type}"' for site_type, _, _, _ in SITE_TYPES),
        Output("locations-display-dummy", "children"),
        Input("map", "bounds"),
        *[
            Input(site_type_id(label), "checked")
            for _, label, _, _ in SITE_TYPES
        ],
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

        # The points layer is always mounted - nothing here adds/removes
        # it; the toggle/filter clientside_callback above controls what's
        # actually visible. That's simpler and more reliable than trying
        # to add/remove the underlying Leaflet layer through
        # dash-leaflet's React lifecycle on every toggle or filter change.
        locations_children = dl.LayerGroup(
            id="locations-points",
            eventHandlers=dict(add=points_layer_handler),
        )

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
