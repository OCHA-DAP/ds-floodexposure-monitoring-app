from dash import html

from layouts.content import content
from layouts.navbar import navbar


def layout(app):
    return html.Div([navbar, content(app)])
