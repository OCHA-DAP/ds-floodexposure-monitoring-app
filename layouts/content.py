import dash_bootstrap_components as dbc
from dash import dcc

from components import dropdowns, text
from components.alerts import geography_alert, internal_alert
from components.plots import rp_plot, timeseries_plot
from constants import NAVBAR_HEIGHT


def content():
    return dbc.Container(
        [
            dbc.Row([dbc.Col([internal_alert])], className="my-2"),
            dbc.Row([dbc.Col([geography_alert])], className="my-2"),
            dbc.Row(
                [
                    dbc.Col(dropdowns.adm_level_dropdown),
                    dbc.Col(dropdowns.get_adm0_dropdown()),
                    dbc.Col(dropdowns.adm1_dropdown),
                    dbc.Col(dropdowns.adm2_dropdown),
                ],
                className="my-2",
            ),
            dbc.Row(
                [dbc.Col([text.timeseries_text, dcc.Loading(timeseries_plot)])],
                className="my-4",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            text.rp_text,
                            dcc.Loading(rp_plot),
                        ]
                    )
                ],
                className="my-4",
            ),
            dbc.Row(
                [dbc.Col([text.data_sources, text.methodology, text.code_references])],
                className="my-4",
            ),
        ],
        style={"marginTop": f"{NAVBAR_HEIGHT}px"},
        className="p-2",
    )
