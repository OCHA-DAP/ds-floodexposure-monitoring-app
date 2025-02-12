from dash import html


def devbar():
    return html.Div(
        "THIS IS A DEV APP",
        style={
            "height": "25px",
            "backgroundColor": "#bf0",
            "textAlign": "center",
        },
    )
