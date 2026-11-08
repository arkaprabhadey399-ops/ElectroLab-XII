
"""Plotly visualization functions for ElectroLab X."""

import pandas as pd
import plotly.graph_objects as go


def make_time_series_chart(
    data: pd.DataFrame,
    y_column: str,
    title: str,
    y_label: str,
    color: str = "#17B8A6",
) -> go.Figure:
    """Create an interactive time-series graph."""

    if "time_s" not in data.columns:
        raise ValueError("Missing time_s column.")

    if y_column not in data.columns:
        raise ValueError(f"Missing {y_column} column.")

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=data["time_s"],
            y=data[y_column],
            mode="lines+markers",
            line=dict(color=color, width=2),
            marker=dict(size=4),
            name=title,
        )
    )

    fig.update_layout(
        title=title,
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Simulation Time (s)",
        yaxis_title=y_label,
        height=340,
        margin=dict(l=20, r=20, t=55, b=30),
        hovermode="x unified",
        showlegend=False,
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="rgba(160,170,190,0.15)",
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(160,170,190,0.15)",
    )

    return fig
