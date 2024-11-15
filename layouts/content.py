import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash_mantine_components as dmc
from dash import dcc, html

from constants import ATTRIBUTION, URL

NAVBAR_HEIGHT = 60 + 48
GUTTER = 15


def content():
    return dbc.Container(
        dbc.Row(
            [
                # ---- Side info bar ----
                dbc.Col(
                    width=3,
                    style={
                        "border": "1px solid #dbdbdb",
                        "backgroundColor": "white",
                        "height": f"calc(100vh - {NAVBAR_HEIGHT + (GUTTER * 2)}px)",
                        "margin": f"{GUTTER}px",
                        "marginRight": f"{GUTTER / 2}px",
                        "minHeight": "500px",
                    },
                    className="g-0",
                    children=info_container(),
                ),
                # ---- Map / chart column ----
                dbc.Col(
                    width=True,
                    style={
                        "backgroundColor": "#f5f5f5",
                        "height": f"calc(100vh - {NAVBAR_HEIGHT + (GUTTER * 2)}px)",
                        "margin": f"{GUTTER}px",
                        "marginLeft": f"{GUTTER / 2}px",
                    },
                    children=[
                        # -- Map --
                        dbc.Row(
                            dbc.Col(map_container()),
                            style={
                                "backgroundColor": "white",
                                "height": f"calc(100% - {300 + GUTTER}px)",
                                "border": "1px solid #dbdbdb",
                                "minHeight": "150px",
                            },
                            className="g-0",
                        ),
                        # -- Chart --
                        dbc.Row(
                            dbc.Col(chart_container()),
                            style={
                                "border": "1px solid #dbdbdb",
                                "backgroundColor": "white",
                                "height": "300px",
                                "marginTop": f"{GUTTER}px",
                                "padding": "5px",
                            },
                            className="g-0",
                        ),
                    ],
                ),
            ],
            style={"backgroundColor": "#f5f5f5"},
        ),
        style={
            "backgroundColor": "red",
            "height": f"calc(100vh - {NAVBAR_HEIGHT}px)",
        },
        fluid=True,
    )


def info_container():
    return html.Div(
        [
            html.Div(
                id="place-name",
                style={"fontWeight": "bold", "fontSize": "24px"},
            ),
            dmc.Space(h=20),
            html.Div(
                id="num-exposed",
                style={"fontSize": "18px"},
            ),
            dmc.Space(h=20),
            dbc.Accordion(
                style={"fontSize": "12px"},
                children=[
                    dbc.AccordionItem(
                        [
                            dcc.Markdown(
                                """
                                Flood extent data is from [Floodscan](https://www.aer.com/weather-risk-management/floodscan-near-real-time-and-historical-flood-mapping/).
                                Population distributions are from [WorldPop](https://www.worldpop.org/). Administrative boundaries are from [FieldMaps](https://fieldmaps.io/).
                                """
                            ),
                        ],
                        title="Data Sources",
                    ),
                    dbc.AccordionItem(
                        [
                            dcc.Markdown(
                                """
                    Daily flood exposure rasters are calculated by multiplying the gridded population (UN adjusted, 1km resolution, 2020)
                    by the 7-day rolling average of the flood extent (SFED_AREA, at a ≈10km resolution), masking out areas where the flood
                    extent is  less than 5% to reduce noise. The daily exposure rasters are then  aggregated to the admin2 level.
                    This is similar to the [method](https://docs.google.com/document/d/16-TrPdCF7dCx5thpdA7dXB8k1MUOJUovWaRVIjEJNUE/edit?tab=t.0#heading=h.rtvq16oq23gp)
                    initially developed for the 2024 Somalia HNRP. Admin0 and admin1 exposure is calculated simply by summing the admin2 exposures.
                    """
                            ),
                            dcc.Markdown(
                                """
                    Return  period is calculated empirically, by ranking each year's flood  exposure. The maximum flood exposure to date
                    for all admin levels is  taken taken as the maximum instantaneous flood exposure for any day in  the year
                    (up to the current day of the year). Note that this does not  take into account flooding in one part of the
                    area on one day and  another part on another day. In this case, the yearly maximum would be  the maximum of these values, not the sum.
                    """
                            ),
                        ],
                        title="Methodology",
                    ),
                    dbc.AccordionItem(
                        dcc.Markdown(
                            """
                        The code used to calculate the daily flood exposure is available on GitHub [here](https://github.com/OCHA-DAP/ds-floodexposure-monitoring).
                        The code used to calculate return period and run this app is available on GitHub [here](https://github.com/OCHA-DAP/ds-floodexposure-monitoring-app).
                        """
                        ),
                        title="Resources",
                    ),
                ],
                flush=True,
            ),
        ],
        id="info-container",
        style={"padding": "15px"},
    )


def map_container():
    return html.Div(
        id="map-container",
        children=[
            dl.Map(
                [dl.TileLayer(url=URL, attribution=ATTRIBUTION)],
                style={"width": "100%", "height": "100%"},
                center=[0, 0],
                zoom=2,
                id="map",
            ),
            dmc.Select(
                id="adm-level",
                value="1",
                data=[
                    {"value": "0", "label": "Admin 0"},
                    {"value": "1", "label": "Admin 1"},
                    {"value": "2", "label": "Admin 2"},
                ],
                style={
                    "width": 130,
                    "position": "absolute",
                    "top": "10px",
                    "right": "20px",
                    "zIndex": 999,
                },
            ),
            dmc.Text(
                id="hover-place-name",
                style={
                    "position": "absolute",
                    "top": "50px",
                    "right": "20px",
                    "zIndex": 999,
                },
            ),
        ],
        style={"width": "100%", "height": "100%", "position": "relative"},
    )


def chart_container():
    exposure_tab = html.Div(
        style={"backgroundColor": "white", "width": "100%", "height": "100%"},
        children=dmc.LoadingOverlay(
            html.Div(id="exposure-chart"), style={"height": "100%"}
        ),
    )
    severity_tab = html.Div(
        style={"backgroundColor": "white", "width": "100%", "height": "100%"},
        children=dmc.LoadingOverlay(html.Div(id="rp-chart"), style={"height": "100%"}),
    )
    return dbc.Tabs(
        [
            dbc.Tab(exposure_tab, label="Timeseries", tabClassName="ms-auto"),
            dbc.Tab(severity_tab, label="Return Period"),
        ]
    )
