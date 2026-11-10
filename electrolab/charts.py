
"""Plotly visualization functions for ElectroLab X."""
import math
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


def make_deposition_comparison_chart(
    theoretical_mg: float,
    actual_mg: float,
) -> go.Figure:
    """Compare predicted and entered final copper mass gain."""

    if not all(
        math.isfinite(value)
        for value in (theoretical_mg, actual_mg)
    ):
        raise ValueError("Mass values must be finite.")

    if theoretical_mg <= 0 or actual_mg < 0:
        raise ValueError("Invalid copper mass values.")

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=["Theoretical", "Actual"],
            y=[theoretical_mg, actual_mg],
            marker_color=["#FB923C", "#17B8A6"],
            text=[
                f"{theoretical_mg:.3f} mg",
                f"{actual_mg:.3f} mg",
            ],
            textposition="outside",
            hovertemplate="%{x}: %{y:.3f} mg<extra></extra>",
        )
    )

    fig.update_layout(
        title="Final Copper Deposition Comparison",
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Copper Mass Gain (mg)",
        yaxis=dict(rangemode="tozero"),
        height=400,
        margin=dict(l=30, r=30, t=60, b=40),
        showlegend=False,
    )

    return fig


