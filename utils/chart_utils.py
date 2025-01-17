import plotly.graph_objects as go

from constants import CHD_BLUE, CHD_GREY, CHD_RED, CUR_YEAR, ROLLING_WINDOW


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
        color = CHD_BLUE
        linewidth = 3 if year == CUR_YEAR else 0.2

        df_year = df_processed[df_processed["date"].dt.year == year]
        fig.add_trace(
            go.Scatter(
                x=df_year["eff_date"],
                y=df_year[f"roll{ROLLING_WINDOW}"],
                name=str(year),
                mode="lines",
                line_color=color,
                line_width=linewidth,
            )
        )

    # Highlight most recent date
    date_max = df_processed.date.max()
    date_1900 = date_max.replace(year=1900)
    date_1900 = date_1900.timestamp() * 1000
    date_formatted = date_max.strftime("%Y-%m-%d")

    fig.add_vline(
        x=date_1900,
        line_dash="dash",
        line_color=CHD_GREY,
        line_width=1,
        opacity=1,
        annotation_text=f"  Data updated<br>{date_formatted}",
        annotation_position="top right",
        annotation_font_color=CHD_GREY,
    )

    fig.update_layout(
        template="simple_white",
        xaxis=dict(
            tickformat="%b",
            dtick="M1",
            showticklabels=True,
            ticklen=0,
            title=None,
            color=CHD_GREY,
        ),
        yaxis=dict(ticklen=0),
        legend_title="Year<br><sup>(click to toggle)</sup>",
        height=240,
        margin={"t": 10, "l": 0, "r": 0, "b": 0},
        font=dict(
            family="Source Sans Pro, sans-serif",
            color="#888888",  # Colors all text
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=11,
            font_family="Source Sans Pro, sans-serif",
        ),
    )

    y_max = df_processed[f"roll{ROLLING_WINDOW}"].max()
    tick_interval = round(y_max / 4, -3)

    fig.update_yaxes(
        title="Population",
        color=CHD_GREY,
        dtick=tick_interval,
        showgrid=True,
        gridwidth=1,
        gridcolor="#eeeeee",
        zeroline=False,
    )
    fig.update_xaxes(range=["1900-01-01", "1900-12-31"])

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
            line_color="#353535",
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
            marker_color=CHD_BLUE,
            textfont=dict(size=15, color=CHD_BLUE),
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
            marker_color=CHD_RED,
            textfont=dict(size=12, color=CHD_RED),
            marker_size=5,
        )
    )

    y_max = df_peaks[f"roll{ROLLING_WINDOW}"].max()
    tick_interval = round(y_max / 4, -3)

    fig.update_layout(
        template="simple_white",
        xaxis=dict(dtick=5, ticklen=0, color=CHD_GREY),
        yaxis=dict(
            ticklen=0,
            dtick=tick_interval,
            color=CHD_GREY,
            showgrid=True,
            gridwidth=1,
            gridcolor="#eeeeee",
            zeroline=False,
        ),
        height=240,
        showlegend=False,
        margin={"t": 10, "l": 0, "r": 0, "b": 0},
        font=dict(family="Arial, sans-serif"),
        hoverlabel=dict(
            bgcolor="white",
            font_size=11,
            font_family="Source Sans Pro, sans-serif",
        ),
    )
    fig.update_yaxes(title="Maximum population exposed")
    fig.update_xaxes(title="Return period (years)")

    return fig
