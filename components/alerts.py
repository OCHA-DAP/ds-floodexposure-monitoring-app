import dash_bootstrap_components as dbc
from dash import html

internal_alert = dbc.Alert(
    [
        "This is an internal tool under development. "
        "For any enquires please contact the OCHA Centre for Humanitarian "
        "Data via Tristan Downing at ",
        html.A("tristan.downing@un.org", href="mailto:tristan.downing@un.org"),
        ".",
    ],
    color="danger",
    dismissable=True,
)

geography_alert = dbc.Alert(
    [
        "Results may vary widely between different geographies "
        "(such as desert vs. wetlands). These differences have not yet been "
        "thoroughly analyzed; the use of this data to compare flood impact "
        "between geographies is not recommended.",
    ],
    color="warning",
    dismissable=True,
)
