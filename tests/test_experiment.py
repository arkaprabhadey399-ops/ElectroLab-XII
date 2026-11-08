import pytest

from electrolab.experiment import ChargeIntegrator


def test_constant_current():
    integrator = ChargeIntegrator()
    integrator.start()

    integrator.add_measurement(0.0, 0.5)
    integrator.add_measurement(1.0, 0.5)
    integrator.add_measurement(2.0, 0.5)

    assert integrator.total_charge_c == pytest.approx(1.0)


def test_varying_current():
    integrator = ChargeIntegrator()
    integrator.start()

    integrator.add_measurement(0.0, 0.2)
    integrator.add_measurement(2.0, 0.4)

    assert integrator.total_charge_c == pytest.approx(0.6)


def test_pause_and_resume():
    integrator = ChargeIntegrator()
    integrator.start()

    integrator.add_measurement(0.0, 0.5)
    integrator.add_measurement(1.0, 0.5)

    integrator.pause()
    integrator.add_measurement(10.0, 0.5)

    integrator.start()
    integrator.add_measurement(20.0, 0.5)
    integrator.add_measurement(21.0, 0.5)

    assert integrator.total_charge_c == pytest.approx(1.0)


def test_disconnection_gap():
    integrator = ChargeIntegrator(max_gap_s=3.0)
    integrator.start()

    integrator.add_measurement(0.0, 0.5)
    integrator.add_measurement(1.0, 0.5)

    # No integration across this long gap.
    integrator.add_measurement(10.0, 0.5)
    integrator.add_measurement(11.0, 0.5)

    assert integrator.total_charge_c == pytest.approx(1.0)


def test_invalid_measurement():
    integrator = ChargeIntegrator()
    integrator.start()

    integrator.add_measurement(0.0, 0.5)

    with pytest.raises(ValueError):
        integrator.add_measurement(1.0, float("nan"))

    # The next valid reading establishes a new baseline.
    integrator.add_measurement(2.0, 0.5)

    assert integrator.total_charge_c == pytest.approx(0.0)


def test_reset():
    integrator = ChargeIntegrator()
    integrator.start()

    integrator.add_measurement(0.0, 0.5)
    integrator.add_measurement(2.0, 0.5)

    integrator.reset()

    assert integrator.total_charge_c == 0.0
    assert integrator.running is False

