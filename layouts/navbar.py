import dash_bootstrap_components as dbc
from dash import html

from constants import CHD_MINT, NAVBAR_HEIGHT


def navbar():
    return dbc.Navbar(
        dbc.Container(
            [
                html.A(
                    dbc.Row(
                        [
                            dbc.Col(
                                dbc.NavbarBrand(
                                    "Risk Monitoring Dashboard",
                                    className=["ms-2", "header", "bold"],
                                )
                            ),
                        ],
                        align="center",
                        className="g-0",
                    ),
                    href="https://centre.humdata.org/data-science/",
                    style={"textDecoration": "none"},
                ),
                dbc.Col(
                    html.Img(
                        src="assets/centreforHumdata_white_TransparentBG.png",
                        height=40,
                        style={
                            "position": "absolute",
                            "right": "15px",
                            "top": "10px",
                        },
                    ),
                ),
            ],
            fluid=True,
        ),
        style={
            "height": f"{NAVBAR_HEIGHT}px",
            "margin": "0px",
            "padding": "10px",
        },
        color=CHD_MINT,
        dark=True,
    )


def module_bar():
    return html.Div(
        "Flood Exposure Module",
        style={
            "backgroundColor": "#353535",
            "color": "white",
            "padding": "6px",
            "paddingLeft": "30px",
            "fontSize": "20px",
        },
        className="header",
    )
