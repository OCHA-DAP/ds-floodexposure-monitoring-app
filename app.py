import dash_bootstrap_components as dbc
from dash import Dash, html

from callbacks.callbacks import register_callbacks
from layouts.content import content
from layouts.navbar import navbar

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Flood Exposure Monitoring"
app._favicon = "assets/favicon.ico"
server = app.server

app.layout = html.Div([navbar, content()])
register_callbacks(app)


if __name__ == "__main__":
    app.run_server(debug=True)
