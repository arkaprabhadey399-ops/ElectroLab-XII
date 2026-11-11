
"""Scientific processing of Arduino serial measurements."""

from dataclasses import dataclass

from electrolab.calculations import theoretical_copper_mass
from electrolab.protocol import ArduinoSample
from electrolab.serial_reader import SerialEvent


@dataclass(frozen=True)
class ProcessedMeasurement:
    time_s: float
    bus_voltage_v: float
    current_ma: float
    bus_power_w: float
    charge_c: float
    copper_mg: float
    continuous: bool
    source: str = "ARDUINO_MOCK"


class ArduinoMeasurementProcessor:
    """Integrate charge from consecutive, valid Arduino packets."""

    def __init__(self, max_gap_s: float = 2.0):
        if max_gap_s <= 0:
            raise ValueError("Maximum gap must be positive.")

        self.max_gap_s = max_gap_s
        self.total_charge_c = 0.0
        self.previous: ArduinoSample | None = None
        self.paused = False

    def pause(self):
        """Break integration continuity while paused."""
        self.paused = True
        self.previous = None

    def resume(self):
        """Resume with a fresh measurement baseline."""
        self.paused = False
        self.previous = None

    def reset(self):
        """Clear all accumulated results."""
        self.total_charge_c = 0.0
        self.previous = None
        self.paused = False

    def process(
        self,
        event: SerialEvent,
    ) -> ProcessedMeasurement | None:
        """Process one validated serial event."""

        if event.status != "sample" or event.sample is None:
            self.previous = None
            return None

        if self.paused:
            self.previous = None
            return None

        sample = event.sample

        # Negative current is not treated as copper deposition.
        # Its physical meaning must be verified during calibration.
        if sample.current_ma < 0:
            self.previous = None
            return None

        valid_interval = False

        if self.previous is not None and event.continuous:
            dt = (
                sample.uptime_ms - self.previous.uptime_ms
            ) / 1000.0

            valid_interval = (
                sample.sequence == self.previous.sequence + 1
                and 0 < dt <= self.max_gap_s
            )

            if valid_interval:
                previous_current_a = (
                    self.previous.current_ma / 1000.0
                )
                current_a = sample.current_ma / 1000.0

                # Trapezoidal integration
                delta_charge = (
                    0.5
                    * (previous_current_a + current_a)
                    * dt
                )

                self.total_charge_c += delta_charge

        self.previous = sample

        theoretical_g = theoretical_copper_mass(
            self.total_charge_c
        )

        return ProcessedMeasurement(
            time_s=sample.uptime_ms / 1000.0,
            bus_voltage_v=sample.bus_voltage_v,
            current_ma=sample.current_ma,
            bus_power_w=(
                sample.bus_voltage_v
                * sample.current_ma / 1000.0
            ),
            charge_c=self.total_charge_c,
            copper_mg=theoretical_g * 1000.0,
            continuous=valid_interval,
        )

    @property
    def theoretical_mass_g(self) -> float:
        """Theoretical copper mass in grams."""
        return theoretical_copper_mass(self.total_charge_c)

    @property
    def theoretical_mass_mg(self) -> float:
        """Theoretical copper mass in milligrams."""
        return self.theoretical_mass_g * 1000.0




