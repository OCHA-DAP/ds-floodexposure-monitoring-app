import dash_bootstrap_components as dbc
from dash import html

from components.alerts import internal_alert


def content(app):
    return dbc.Container(
        [
            dbc.Row([dbc.Col([internal_alert])], className="my-2"),
            dbc.Row(
                [dbc.Col([html.H1(app.data["adm"].iloc[0]["ADM2_PCODE"])])],
                className="my-2",
            ),
        ],
        style={"marginTop": "60px"},
        className="p-2",
    )
