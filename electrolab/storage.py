import csv
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


"""Data export utilities for ElectroLab X."""

import pandas as pd

MEASUREMENT_COLUMNS = [
    "time_s",
    "voltage_v",
    "current_ma",
    "power_w",
    "charge_c",
    "copper_mg",
    "source",
]


def measurements_to_csv(history: list[dict]) -> str:
    """Convert measurement history to CSV text."""

    if not history:
        raise ValueError("There are no measurements to export.")

    for index, row in enumerate(history):
        missing = set(MEASUREMENT_COLUMNS) - set(row)

        if missing:
            raise ValueError(
                f"Measurement {index} is missing: {sorted(missing)}"
            )

    df = pd.DataFrame(
        history,
        columns=MEASUREMENT_COLUMNS,
    )

    return df.to_csv(index=False)


def create_experiment_log(
    directory: Path | None = None,
) -> Path:
    """Create a uniquely named CSV file for a new experiment."""

    if directory is None:
        directory = Path(__file__).resolve().parent.parent / "data"

    directory.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S"
    )

    unique_id = uuid4().hex[:8]

    file_path = directory / (
        f"ElectroLab_{timestamp}_{unique_id}.csv"
    )

    with file_path.open(
        "x", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=MEASUREMENT_COLUMNS,
        )
        writer.writeheader()

    return file_path


def append_measurement(
    file_path: Path,
    measurement: dict,
) -> None:
    """Append one validated measurement record to disk."""

    missing = set(MEASUREMENT_COLUMNS) - set(measurement)

    if missing:
        raise ValueError(
            f"Missing measurement fields: {sorted(missing)}"
        )

    if not file_path.is_file():
        raise FileNotFoundError(
            f"Experiment log does not exist: {file_path}"
        )

    with file_path.open(
        "a", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=MEASUREMENT_COLUMNS,
        )

        writer.writerow({
            column: measurement[column]
            for column in MEASUREMENT_COLUMNS
        })


