import pytest

from electrolab.simulation import ElectroplatingSimulator
from electrolab.experiment import ChargeIntegrator


def test_measurement_units_and_values():
    simulator = ElectroplatingSimulator()
    sample = simulator.next_measurement()

    assert sample.timestamp_s == 0.0
    assert sample.voltage_v > 0
    assert sample.current_a >= 0
    assert sample.source == "SIMULATION"
    assert sample.power_w == pytest.approx(
        sample.voltage_v * sample.current_a
    )


def test_sampling_interval():
    simulator = ElectroplatingSimulator(
        sample_interval_s=0.5
    )

    first = simulator.next_measurement()
    second = simulator.next_measurement()

    assert second.timestamp_s - first.timestamp_s == pytest.approx(0.5)


def test_reproducible_simulation():
    simulator_a = ElectroplatingSimulator(seed=123)
    simulator_b = ElectroplatingSimulator(seed=123)

    for _ in range(20):
        assert (
            simulator_a.next_measurement()
            == simulator_b.next_measurement()
        )


def test_current_adjustment():
    normal = ElectroplatingSimulator(seed=42)
    adjusted = ElectroplatingSimulator(seed=42)

    adjusted.set_current_multiplier(1.5)

    first = normal.next_measurement()
    second = adjusted.next_measurement()

    assert second.current_a > first.current_a


def test_simulation_with_charge_integrator():
    simulator = ElectroplatingSimulator()
    integrator = ChargeIntegrator()
    integrator.start()

    for _ in range(100):
        sample = simulator.next_measurement()
        integrator.add_measurement(
            sample.timestamp_s,
            sample.current_a,
        )

    assert integrator.total_charge_c > 0
    assert integrator.theoretical_mass_mg > 0


def test_invalid_sampling_interval():
    with pytest.raises(ValueError):
        ElectroplatingSimulator(sample_interval_s=0)


def test_invalid_current_multiplier():
    simulator = ElectroplatingSimulator()

    with pytest.raises(ValueError):
        simulator.set_current_multiplier(-1)

