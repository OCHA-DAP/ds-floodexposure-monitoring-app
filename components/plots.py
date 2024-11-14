from dash import dcc

timeseries_plot = dcc.Graph(id="timeseries", config={"displayModeBar": False})
rp_plot = dcc.Graph(id="rp", config={"displayModeBar": False})
