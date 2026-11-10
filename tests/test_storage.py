from electrolab.storage import (
    create_experiment_log,
    append_measurement,
)
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



def test_automatic_log_creation_and_append(tmp_path):
    # Create a CSV file in a temporary directory.
    path = create_experiment_log(tmp_path)

    assert path.exists()

    measurement = {
        "time_s": 0.5,
        "voltage_v": 4.0,
        "current_ma": 450.0,
        "power_w": 1.8,
        "charge_c": 0.225,
        "copper_mg": 0.074,
        "source": "SIMULATION",
    }

    # Save the measurement.
    append_measurement(path, measurement)

    # Read the file and verify the saved data.
    with path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    assert len(rows) == 1
    assert float(rows[0]["current_ma"]) == 450.0
    assert rows[0]["source"] == "SIMULATION"


def test_unique_experiment_filenames(tmp_path):
    first = create_experiment_log(tmp_path)
    second = create_experiment_log(tmp_path)

    assert first != second
    assert first.exists()
    assert second.exists()


def test_invalid_measurement_record(tmp_path):
    path = create_experiment_log(tmp_path)

    incomplete_measurement = {
        "time_s": 1.0,
        "voltage_v": 4.0,
    }

    with pytest.raises(ValueError):
        append_measurement(path, incomplete_measurement)
