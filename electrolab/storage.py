
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
