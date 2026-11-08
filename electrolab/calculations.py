"""Scientific calculations for ElectroLab X."""

import math

# Physical constants
COPPER_MOLAR_MASS = 63.546  # g/mol
FARADAY_CONSTANT = 96485.0  # C/mol
COPPER_VALENCE = 2


def electrical_power(voltage_v: float, current_a: float) -> float:
    """Calculate electrical power in watts."""
    if not all(math.isfinite(x) for x in (voltage_v, current_a)):
        raise ValueError("Voltage and current must be finite.")
    return voltage_v * current_a


def charge_increment(
    previous_current_a: float,
    current_a: float,
    delta_time_s: float,
) -> float:
    """Integrate current over one valid time interval."""
    values = (previous_current_a, current_a, delta_time_s)

    if not all(math.isfinite(x) for x in values):
        raise ValueError("Inputs must be finite.")

    if delta_time_s <= 0:
        raise ValueError("Time interval must be positive.")

    return 0.5 * (
        previous_current_a + current_a
    ) * delta_time_s


def theoretical_copper_mass(charge_c: float) -> float:
    """Calculate theoretical copper deposition in grams."""
    if not math.isfinite(charge_c) or charge_c < 0:
        raise ValueError("Charge must be finite and non-negative.")

    return (
        COPPER_MOLAR_MASS * charge_c
        / (COPPER_VALENCE * FARADAY_CONSTANT)
    )
def current_density(current_a: float, area_cm2: float) -> float:
    """Return current density in A/cm²."""
    if not math.isfinite(current_a):
        raise ValueError("Current must be finite.")

    if not math.isfinite(area_cm2) or area_cm2 <= 0:
        raise ValueError("Area must be positive and finite.")

    return current_a / area_cm2


def actual_mass_gain(
    initial_mass_g: float,
    final_mass_g: float,
) -> float:
    """Return measured cathode mass gain in grams."""
    if not all(math.isfinite(x) for x in (initial_mass_g, final_mass_g)):
        raise ValueError("Mass measurements must be finite.")

    if initial_mass_g < 0 or final_mass_g < 0:
        raise ValueError("Mass measurements cannot be negative.")

    return final_mass_g - initial_mass_g


def current_efficiency(
    actual_mass_g: float,
    theoretical_mass_g: float,
) -> float:
    """Return apparent current efficiency as a percentage."""
    if not all(math.isfinite(x) for x in (actual_mass_g, theoretical_mass_g)):
        raise ValueError("Mass values must be finite.")

    if theoretical_mass_g <= 0:
        raise ValueError("Theoretical mass must be positive.")

    return (actual_mass_g / theoretical_mass_g) * 100