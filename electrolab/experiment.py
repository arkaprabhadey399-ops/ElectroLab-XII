"""Experiment measurement and charge integration."""

import math

from electrolab.calculations import (
    charge_increment,
    theoretical_copper_mass,
)


class ChargeIntegrator:
    """Accumulate charge from valid current measurements."""

    def __init__(self, max_gap_s: float = 3.0):
        if not math.isfinite(max_gap_s) or max_gap_s <= 0:
            raise ValueError("Maximum gap must be positive.")

        self.max_gap_s = max_gap_s
        self.reset()

    def reset(self):
        """Clear all measurements and accumulated charge."""
        self.total_charge_c = 0.0
        self.previous_time_s = None
        self.previous_current_a = None
        self.running = False

    def start(self):
        """Begin or resume measurement integration."""
        self.running = True
        self._clear_previous()

    def pause(self):
        """Pause integration without clearing total charge."""
        self.running = False
        self._clear_previous()

    def _clear_previous(self):
        """Break continuity with the previous sample."""
        self.previous_time_s = None
        self.previous_current_a = None

    def add_measurement(
        self,
        timestamp_s: float,
        current_a: float,
    ) -> float:
        """Process a measurement and return total charge."""
        if not self.running:
            return self.total_charge_c

        if not (
            math.isfinite(timestamp_s)
            and math.isfinite(current_a)
        ):
            self._clear_previous()
            raise ValueError("Measurement must be finite.")

        # Convention: positive current means copper deposition.
        if current_a < 0:
            self._clear_previous()
            raise ValueError("Negative plating current.")

        if self.previous_time_s is not None:
            dt = timestamp_s - self.previous_time_s

            if dt <= 0:
                self._clear_previous()
                raise ValueError("Timestamps must increase.")

            if dt <= self.max_gap_s:
                assert self.previous_current_a is not None
                increment = charge_increment(
                    self.previous_current_a,
                    current_a,
                    dt,
                )
                self.total_charge_c += increment

        self.previous_time_s = timestamp_s
        self.previous_current_a = current_a

        return self.total_charge_c

    @property
    def theoretical_mass_g(self) -> float:
        """Predicted deposited copper mass, in grams."""
        return theoretical_copper_mass(self.total_charge_c)

    @property
    def theoretical_mass_mg(self) -> float:
        """Predicted deposited copper mass, in milligrams."""
        return self.theoretical_mass_g * 1000

