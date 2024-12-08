from dash import Dash, dcc
from utils.log_utils import setup_logging

from callbacks.callbacks import register_callbacks
from layouts.content import content
from layouts.modal import disclaimer_modal
from layouts.navbar import module_bar, navbar

app = Dash(__name__, update_title=None, suppress_callback_exceptions=True)
server = app.server
app.title = "Flood Exposure"

logger = setup_logging()

register_callbacks(app)
app.layout = [
    disclaimer_modal(),
    navbar(),
    module_bar(),
    content(),
    dcc.Store(id="selected-pcode"),
]


if __name__ == "__main__":
    app.run_server(debug=True)
