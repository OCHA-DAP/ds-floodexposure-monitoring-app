import json
from functools import lru_cache

from dash import Dash, dcc
from flask import Response

from callbacks.callbacks import register_callbacks
from constants import STAGE
from layouts.content import content
from layouts.devbar import devbar
from layouts.modal import disclaimer_modal
from layouts.navbar import module_bar, navbar
from utils.data_utils import get_locations_geojson
from utils.log_utils import setup_logging

app = Dash(__name__, update_title=None, suppress_callback_exceptions=True)
server = app.server
app.title = "Sudan Flood Exposure"

logger = setup_logging()

register_callbacks(app)


@lru_cache(maxsize=1)
def _locations_json_body():
    # get_locations_geojson() caches the parsed dict, but without this
    # every request would still re-run json.dumps() over all ~12k
    # features - cache the serialized body too.
    return json.dumps(get_locations_geojson())


@server.route("/data/locations.json")
def locations_geojson():
    # Served as a static-style route (rather than a dcc.Store/callback
    # payload) so the ~12k-point dataset is fetched once by the browser
    # and cached, instead of being re-sent on every map callback.
    return Response(_locations_json_body(), mimetype="application/json")


layout = [
    dcc.Location(id="url", refresh=False),
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
    app.run(debug=True)
