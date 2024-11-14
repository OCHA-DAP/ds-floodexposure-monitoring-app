import dash_bootstrap_components as dbc
from dash import Dash

from callbacks.callbacks import register_callbacks
from data.load_data import load_data
from endpoints.endpoints import register_endpoints
from index import layout

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Flood Exposure Monitoring"
app._favicon = "assets/favicon.ico"
server = app.server

app.data = load_data()

app.layout = layout(app)
register_callbacks(app)
register_endpoints(app)

if __name__ == "__main__":
    app.run(debug=True)
