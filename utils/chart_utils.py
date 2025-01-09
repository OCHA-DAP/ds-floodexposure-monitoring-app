import plotly.graph_objects as go

from constants import CHD_GREEN, CUR_YEAR, ROLLING_WINDOW


def create_timeseries_plot(df_seasonal, df_processed, peak_years):
    """Create timeseries plot using Plotly."""
    df_seasonal = df_seasonal.sort_values("eff_date")
    df_processed = df_processed.sort_values("date", ascending=False)
    fig = go.Figure()

    # Add seasonal average
    fig.add_trace(
        go.Scatter(
            x=df_seasonal["eff_date"],
            y=df_seasonal[f"roll{ROLLING_WINDOW}"],
            name="Average",
            line_color="black",
            line_width=2,
        )
    )

    # Add yearly traces
    for year in df_processed["date"].dt.year.unique():
        color = (
            CHD_GREEN
            if year == CUR_YEAR
            else "red"
            if year in peak_years
            else "grey"
        )
        linewidth = 3 if year == CUR_YEAR else 0.2

        df_year = df_processed[df_processed["date"].dt.year == year]
        fig.add_trace(
            go.Scatter(
                x=df_year["eff_date"],
                y=df_year[f"roll{ROLLING_WINDOW}"],
                name=str(year),
                line_color=color,
                line_width=linewidth,
            )
        )

    fig.update_layout(
        template="simple_white",
        xaxis=dict(tickformat="%b %d", dtick="M1"),
        legend_title="Year<br><sup>(click to toggle)</sup>",
        height=340,
        margin={"t": 10, "l": 0, "r": 0, "b": 0},
        font=dict(family="Arial, sans-serif"),
    )
    fig.update_yaxes(
        rangemode="tozero", title="Population exposed to flooding"
    )
    # set x max to year 1900
    fig.update_xaxes(title="Date", range=["1900-01-01", "1900-12-31"])

    return fig


def create_return_period_plot(df_peaks, rp=3):
    """Create return period plot using Plotly."""
    fig = go.Figure()

    # Add all years trace
    fig.add_trace(
        go.Scatter(
            x=df_peaks["rp"],
            y=df_peaks[f"roll{ROLLING_WINDOW}"],
            name="all years",
            mode="lines",
            line_color="black",
        )
    )

    # Add point for current year
    df_peak_cur = df_peaks.set_index("date").loc[CUR_YEAR]
    position = (
        "bottom left"
        if df_peak_cur["rank"] == 1
        else (
            "top right"
            if df_peak_cur["rank"] == len(df_peaks)
            else "bottom right"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[df_peak_cur["rp"]],
            y=[df_peak_cur[f"roll{ROLLING_WINDOW}"]],
            name="current year",
            mode="markers+text",
            text=CUR_YEAR,
            textposition=position,
            marker_color=CHD_GREEN,
            textfont=dict(size=15, color=CHD_GREEN),
            marker_size=10,
        )
    )

    # Add other significant years
    df_rp_peaks = df_peaks[
        (df_peaks[f"{rp}yr_rp"]) & (df_peaks["date"] != CUR_YEAR)
    ]
    fig.add_trace(
        go.Scatter(
            x=df_rp_peaks["rp"],
            y=df_rp_peaks[f"roll{ROLLING_WINDOW}"],
            text=df_rp_peaks["date"],
            name="≥3-yr RP years",
            textposition="top left",
            mode="markers+text",
            marker_color="red",
            textfont=dict(size=12, color="red"),
            marker_size=5,
        )
    )

    fig.update_layout(
        template="simple_white",
        xaxis=dict(dtick=1),
        height=340,
        showlegend=False,
        margin={"t": 10, "l": 0, "r": 0, "b": 0},
        font=dict(family="Arial, sans-serif"),
    )
    fig.update_yaxes(title="Maximum daily flood exposure during year")
    fig.update_xaxes(title="Return period (years)")

    return fig
