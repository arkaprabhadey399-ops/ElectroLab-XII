"""Synthetic electrical measurements for ElectroLab X."""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SimulatedMeasurement:
    timestamp_s: float
    voltage_v: float
    current_a: float
    source: str = "SIMULATION"

    @property
    def power_w(self) -> float:
        return self.voltage_v * self.current_a


class ElectroplatingSimulator:
    """Generate reproducible, sensor-like measurements."""

    def __init__(
        self,
        voltage_v: float = 4.0,
        current_a: float = 0.45,
        sample_interval_s: float = 0.5,
        seed: int | None = 42,
    ):
        if not np.isfinite(voltage_v) or voltage_v <= 0:
            raise ValueError("Voltage must be positive and finite.")

        if not np.isfinite(current_a) or current_a <= 0:
            raise ValueError("Current must be positive and finite.")

        if (
            not np.isfinite(sample_interval_s)
            or sample_interval_s <= 0
        ):
            raise ValueError("Sample interval must be positive.")

        self.nominal_voltage_v = voltage_v
        self.nominal_current_a = current_a
        self.sample_interval_s = sample_interval_s

        self.rng = np.random.default_rng(seed)
        self.time_s = 0.0
        self.sample_count = 0

        # Fractional decrease in current per second.
        self.drift_rate = 0.00005

        self.current_multiplier = 1.0

    def set_current_multiplier(self, multiplier: float):
        """Simulate a controlled change in current."""
        if not np.isfinite(multiplier) or multiplier <= 0:
            raise ValueError("Multiplier must be positive.")

        self.current_multiplier = multiplier

    def next_measurement(self) -> SimulatedMeasurement:
        """Generate one synthetic voltage/current sample."""

        # Small random fluctuations.
        current_noise = self.rng.normal(0.0, 0.003)
        voltage_noise = self.rng.normal(0.0, 0.015)

        drift = max(
            0.80,
            1.0 - self.drift_rate * self.time_s,
        )

        current = (
            self.nominal_current_a
            * self.current_multiplier
            * drift
            + current_noise
        )

        voltage = self.nominal_voltage_v + voltage_noise

        measurement = SimulatedMeasurement(
            timestamp_s=self.time_s,
            voltage_v=max(0.0, float(voltage)),
            current_a=max(0.0, float(current)),
        )

        self.sample_count += 1
        self.time_s += self.sample_interval_s

        return measurement
