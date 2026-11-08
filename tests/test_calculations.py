import pytest

from electrolab.calculations import (
    electrical_power,
    charge_increment,
    theoretical_copper_mass,
)


def test_electrical_power():
    assert electrical_power(5.0, 0.4) == pytest.approx(2.0)


def test_constant_current_charge():
    # 0.5 A flowing for 10 seconds gives 5 C.
    assert charge_increment(0.5, 0.5, 10.0) == pytest.approx(5.0)


def test_varying_current_charge():
    # Current changes linearly from 0.2 A to 0.6 A.
    assert charge_increment(0.2, 0.6, 10.0) == pytest.approx(4.0)


def test_one_mole_of_copper():
    # Two moles of electrons deposit one mole of copper.
    charge = 2 * 96485.0
    assert theoretical_copper_mass(charge) == pytest.approx(63.546)


def test_invalid_time_interval():
    with pytest.raises(ValueError):
        charge_increment(0.4, 0.5, 0)


def test_negative_deposition_charge():
    with pytest.raises(ValueError):
        theoretical_copper_mass(-5.0)

from electrolab.calculations import (
    current_density,
    actual_mass_gain,
    current_efficiency,
)
def test_current_density():
    assert current_density(0.5, 10.0) == pytest.approx(0.05)


def test_current_density_invalid_area():
    with pytest.raises(ValueError):
        current_density(0.5, 0)


def test_actual_mass_gain():
    assert actual_mass_gain(12.5, 12.6) == pytest.approx(0.1)


def test_current_efficiency():
    assert current_efficiency(0.085, 0.100) == pytest.approx(85.0)


def test_efficiency_above_100():
    assert current_efficiency(0.11, 0.10) == pytest.approx(110.0)


