import dash_bootstrap_components as dbc
from dash import dcc


def disclaimer_modal():
    return dbc.Modal(
        [
            dbc.ModalHeader(
                dbc.ModalTitle("Disclaimer", className="header"),
                close_button=True,
            ),
            dbc.ModalBody(
                [
                    dcc.Markdown(
                        """
                        This is an internal tool under development. For any enquiries please
                        contact the OCHA Centre for Humanitarian Data via Tristan Downing at
                        [tristan.downing@un.org](mailto:tristan.downing@un.org).
                        """
                    ),
                    dcc.Markdown(
                        """
                            Results may vary widely between different geographies
                            (such as desert vs. wetlands). These differences have not yet been
                            thoroughly analyzed; the use of this data to compare flood exposure
                            between geographies is not recommended.
                            """
                    ),
                ]
            ),
        ],
        id="modal",
        is_open=True,
        centered=True,
    )
