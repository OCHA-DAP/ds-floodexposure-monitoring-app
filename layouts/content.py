import dash_bootstrap_components as dbc

from components import dropdowns
from components.alerts import geography_alert, internal_alert
from components.plots import rp_plot, timeseries_plot


def content(app):
    return dbc.Container(
        [
            dbc.Row([dbc.Col([internal_alert])], className="my-2"),
            dbc.Row([dbc.Col([geography_alert])], className="my-2"),
            dbc.Row(
                [
                    dbc.Col(dropdowns.adm_level_dropdown),
                    dbc.Col(dropdowns.get_adm0_dropdown(app)),
                    dbc.Col(dropdowns.adm1_dropdown),
                    dbc.Col(dropdowns.adm2_dropdown),
                ],
                className="my-2",
            ),
            dbc.Row([dbc.Col([timeseries_plot])], className="my-2"),
            dbc.Row([dbc.Col([rp_plot])], className="my-2"),
        ],
        style={"marginTop": "60px"},
        className="p-2",
    )
