import dash_bootstrap_components as dbc

from src.constants import ISO3S

adm_level_dropdown = dbc.InputGroup(
    [
        dbc.InputGroupText("Admin Level"),
        dbc.Select(
            id="adm_level",
            options=[{"label": x, "value": x} for x in range(3)],
            value="0",
        ),
    ],
    size="sm",
)


def get_adm0_dropdown():
    return dbc.InputGroup(
        [
            dbc.InputGroupText("Country"),
            dbc.Select(
                id="iso3",
                options=ISO3S,
                value="tcd",
            ),
        ],
        size="sm",
    )


adm1_dropdown = dbc.InputGroup(
    [
        dbc.InputGroupText("Admin 1"),
        dbc.Select(id="adm1"),
    ],
    size="sm",
)


adm2_dropdown = dbc.InputGroup(
    [
        dbc.InputGroupText("Admin 2"),
        dbc.Select(id="adm2"),
    ],
    size="sm",
)
