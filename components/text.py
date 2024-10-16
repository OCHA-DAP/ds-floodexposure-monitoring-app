from dash import html

timeseries_text = html.Div(
    [
        html.H2("Time Series"),
        html.P(
            "The estimated flood exposure on each day since 1998, "
            "summed over the administrative division."
        ),
    ]
)

rp_text = html.Div(
    [
        html.H2("Return Period"),
        html.P(
            "The return period of the maximum flood exposure to date this "
            "calendar year, compared to the maximum flood exposure up "
            "to the same day in previous years. "
            "The return period is calculated empirically, i.e., by simply "
            "ranking historical years."
        ),
    ]
)

data_sources = html.Div(
    [
        html.H6("Data sources"),
        html.P(
            [
                "Flood extent data is from ",
                html.A(
                    "Floodscan",
                    href="https://www.aer.com/weather-risk-management/"
                    "floodscan-near-real-time-and-historical-flood-mapping/",
                    target="_blank",
                ),
                ". Population distributions are from ",
                html.A(
                    "WorldPop",
                    href="https://www.worldpop.org/",
                    target="_blank",
                ),
                ". Administrative boundaries are from ",
                html.A(
                    "FieldMaps",
                    href="https://fieldmaps.io/",
                    target="_blank",
                ),
                ".",
            ],
        ),
    ],
    style={"color": "grey", "font-size": "0.8rem"},
)

methodology = html.Div(
    [
        html.H6("Methodology"),
        html.P(
            [
                "Daily flood exposure rasters are calculated by multiplying "
                "the gridded population (",
                html.I("UN adjusted, 1km resolution, 2020"),
                ") by the 7-day rolling average of the " "flood extent (",
                html.I("SFED_AREA"),
                ", at a ≈10km resolution), "
                "masking out areas where the flood extent is less than "
                "5% to reduce noise. "
                "The daily exposure rasters are then aggregated to the "
                "admin2 level. "
                "This is similar to the ",
                html.A(
                    "method",
                    href="https://docs.google.com/document/d/"
                    "16-TrPdCF7dCx5thpdA7dXB8k1MUOJUovWaRVIjEJNUE/"
                    "edit#heading=h.rtvq16oq23gp",
                    target="_blank",
                ),
                " initially developed for the "
                "2024 Somalia HNRP. "
                "Admin0 and admin1 exposure is calculated "
                "simply by summing the admin2 exposures.",
            ],
        ),
        html.P(
            [
                "Return period is calculated empirically, by ranking each "
                "year's flood exposure. "
                "The maximum flood exposure to date for all admin levels "
                "is taken taken as the maximum instantaneous flood exposure "
                "for any day in the year (up to the current day of the year). "
                "Note that this does not take into account flooding in one "
                "part of the area on one day and another part on another day. "
                "In this case, the yearly maximum would be the maximum "
                "of these values, not the sum.",
            ]
        ),
    ],
    style={"color": "grey", "font-size": "0.8rem"},
)

code_references = html.Div(
    [
        html.H6("Code"),
        html.P(
            [
                "The code used to calculate the daily flood exposure is "
                "available on GitHub ",
                html.A(
                    "here",
                    href="https://github.com/OCHA-DAP/ds-floodexposure-monitoring",
                    target="_blank",
                ),
                ". The code used to calculate return period and "
                "run this app is available on GitHub ",
                html.A(
                    "here",
                    href="https://github.com/OCHA-DAP/ds-floodexposure-monitoring-app",
                    target="_blank",
                ),
                ".",
            ],
        ),
    ],
    style={"color": "grey", "font-size": "0.8rem"},
)
