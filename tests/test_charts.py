
import pandas as pd
import pytest
import numpy as np

from plotly.graph_objs import Scatter, Bar

from electrolab.charts import (
    make_time_series_chart,
    make_deposition_comparison_chart,
)


def test_current_chart():
    df = pd.DataFrame({
        "time_s": [0.0, 0.5, 1.0],
        "current_ma": [450.0, 455.0, 448.0],
    })

    fig = make_time_series_chart(
        data=df,
        y_column="current_ma",
        title="Current vs Time",
        y_label="Current (mA)",
    )

    
    # Access the first Plotly trace.
    trace = next(fig.select_traces())

    # Tell Pylance exactly which trace type we expect.
    assert isinstance(trace, Scatter)

    # Verify current measurements.
    np.testing.assert_allclose(
        np.asarray(trace.y, dtype=float),
        [450.0, 455.0, 448.0],
    )

    # Verify measurement timestamps.
    np.testing.assert_allclose(
        np.asarray(trace.x, dtype=float),
        [0.0, 0.5, 1.0],
    )



def test_invalid_chart_column():

    df = pd.DataFrame(
        {"time_s": [0, 1, 2]}
    )

    with pytest.raises(ValueError):
        make_time_series_chart(
            data=df,
            y_column="current_ma",
            title="Current",
            y_label="Current (mA)",
        )


def test_deposition_comparison_chart():
    fig = make_deposition_comparison_chart(
        theoretical_mg=2.5,
        actual_mg=2.0,
    )

    trace = next(fig.select_traces())

    
    assert isinstance(trace, Bar)

    # Confirm that the graph has X-axis data.
    x_values = trace.x
    assert x_values is not None

    # Verify the labels.
    assert list(x_values) == ["Theoretical", "Actual"]


    np.testing.assert_allclose(
        np.asarray(trace.y, dtype=float),
        [2.5, 2.0],
    )


def test_invalid_deposition_comparison():
    with pytest.raises(ValueError):
        make_deposition_comparison_chart(
            theoretical_mg=0.0,
            actual_mg=1.0,
        )





