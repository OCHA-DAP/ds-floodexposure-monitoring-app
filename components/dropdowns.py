import dash_bootstrap_components as dbc

from src.constants import ISO3S, iso3_to_pcode

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


def get_adm0_dropdown(app):
    adm = app.data.get("adm")
    return dbc.InputGroup(
        [
            dbc.InputGroupText("Country"),
            dbc.Select(
                id="iso3",
                options=[
                    {
                        "label": adm[adm["ADM0_PCODE"] == iso3_to_pcode.get(x)].iloc[0][
                            "ADM0_NAME"
                        ],
                        "value": x,
                    }
                    for x in ISO3S
                ],
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
