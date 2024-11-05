import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_mantine_components as dmc
from dash import Dash, dcc, html

from callbacks.callbacks import register_callbacks
from constants import ATTRIBUTION, URL
from layouts.navbar import navbar

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

register_callbacks(app)


# adm0_style_handle = assign(
#     """
#     function(feature, context) {
#         const selected = context.hideout.selected
#         const hasData = feature.properties.has_data
#         const fillColor = hasData ? '#1f77b4' : '#d3d3d3';
#         console.log(selected)
#         if(selected.includes(feature.properties.iso_3)){
#             return {
#             fillColor: fillColor,
#             weight: 0.8,
#             opacity: 1,
#             color: 'white',
#             fillOpacity: 0.8
#         }
#         }

#         return {
#             fillColor: fillColor,
#             weight: 0.8,
#             opacity: 1,
#             color: 'white',
#             fillOpacity: 0.3
#         }
#     }
# """
# )


# Create the layout
app.layout = html.Div(
    [
        navbar,
        dmc.Select(
            label="Select admin level",
            id="adm-level",
            value="2",
            data=[
                {"value": "0", "label": "Admin 0"},
                {"value": "1", "label": "Admin 1"},
                {"value": "2", "label": "Admin 2"},
            ],
            style={
                "width": 200,
                "position": "absolute",
                "top": "67px",
                "left": "50px",
                "zIndex": 999,
            },
        ),
        html.Div(
            [
                dl.Map(
                    [dl.TileLayer(url=URL, attribution=ATTRIBUTION)],
                    style={"width": "50%", "height": "80vh"},
                    center=[0, 0],
                    zoom=2,
                    id="map",
                ),
                html.Div(
                    id="charts",
                    style={"backgroundColor": "#D4DADC", "width": "50%"},
                    children=dmc.LoadingOverlay(
                        html.Div(id="figure-div"), style={"height": "80vh"}
                    ),
                ),
            ],
            style={"display": "flex", "marginTop": "60px"},
        ),
        html.Div(
            id="hover-info",
            style={
                "margin": "10px",
                "padding": "10px",
                "backgroundColor": "#f0f0f0",
                "borderRadius": "5px",
            },
        ),
        dcc.Store(id="selected-iso3", data="BFA"),
        dcc.Store(id="selected-pcode", data=""),  # "BF5201"
    ]
)


if __name__ == "__main__":
    app.run_server(debug=True)
