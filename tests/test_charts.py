import pandas as pd
import plotly.graph_objects as go
import pytest
import numpy as np
from plotly.graph_objs import Scatter
from electrolab.charts import make_time_series_chart


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




