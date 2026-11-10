
import pytest

from electrolab.reports import generate_experiment_report


@pytest.fixture
def sample_history():
    return [
        {
            "time_s": 0.0,
            "voltage_v": 4.0,
            "current_ma": 500.0,
            "power_w": 2.0,
            "charge_c": 0.0,
            "source": "SIMULATION",
        },
        {
            "time_s": 1.0,
            "voltage_v": 4.0,
            "current_ma": 500.0,
            "power_w": 2.0,
            "charge_c": 0.5,
            "source": "SIMULATION",
        },
    ]


def test_report_with_mass_measurements(sample_history):
    report = generate_experiment_report(
        history=sample_history,
        experiment_name="Copper Test",
        area_cm2=10.0,
        initial_mass_g=10.0,
        final_mass_g=10.0001,
    )

    assert "Copper Test" in report
    assert "SIMULATION" in report
    assert "Integrated charge: 0.500000 C" in report
    assert "Apparent current efficiency:" in report


def test_report_without_mass_measurements(sample_history):
    report = generate_experiment_report(
        history=sample_history,
        experiment_name="Test",
        area_cm2=10.0,
    )

    assert "Mass comparison: Not available" in report


def test_empty_report_rejected():
    with pytest.raises(ValueError):
        generate_experiment_report(
            history=[],
            experiment_name="Empty",
            area_cm2=10.0,
        )
