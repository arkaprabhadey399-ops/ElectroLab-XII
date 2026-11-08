
import csv
import io

import pytest

from electrolab.storage import measurements_to_csv


def test_csv_export():
    history = [{
        "time_s": 0.0,
        "voltage_v": 4.0,
        "current_ma": 450.0,
        "power_w": 1.8,
        "charge_c": 0.0,
        "copper_mg": 0.0,
        "source": "SIMULATION",
    }]

    output = measurements_to_csv(history)
    rows = list(csv.DictReader(io.StringIO(output)))

    assert len(rows) == 1
    assert float(rows[0]["current_ma"]) == 450.0
    assert rows[0]["source"] == "SIMULATION"


def test_empty_export():
    with pytest.raises(ValueError):
        measurements_to_csv([])


