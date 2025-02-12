from dash import Dash, dcc

from callbacks.callbacks import register_callbacks
from constants import STAGE
from layouts.content import content
from layouts.devbar import devbar
from layouts.modal import disclaimer_modal
from layouts.navbar import module_bar, navbar
from utils.log_utils import setup_logging

app = Dash(__name__, update_title=None, suppress_callback_exceptions=True)
server = app.server
app.title = "Flood Exposure"

logger = setup_logging()

register_callbacks(app)
layout = [
    disclaimer_modal(),
    navbar(),
    module_bar(),
    content(),
    dcc.Store(id="selected-data"),
]

if STAGE == "dev":
    layout.insert(1, devbar())

app.layout = layout


if __name__ == "__main__":
    app.run_server(debug=True)
