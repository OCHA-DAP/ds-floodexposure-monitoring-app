import dash_bootstrap_components as dbc
from dash import html

from constants import NAVBAR_HEIGHT


def navbar():
    return dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(
                                html.Img(
                                    src="assets/centre_banner_greenbg.png", height=40
                                )
                            ),
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "Risk Monitoring Dashboard", className="ms-2"
                                )
                            ),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://centre.humdata.org/data-science/",
                    style={"textDecoration": "none"},
                ),
                dbc.NavbarToggler(id="navbar-toggler", n_clicks=0),
            ]
        ),
        style={"height": f"{NAVBAR_HEIGHT}px", "margin": "0px", "padding": "10px"},
        color="primary",
        dark=True,
    )


def module_bar():
    return html.Div(
        "Flood Exposure Module",
        style={
            "backgroundColor": "#007ce1",
            "color": "white",
            "padding": "6px",
            "paddingLeft": "75px",
            "fontSize": "24px",
        },
    )
