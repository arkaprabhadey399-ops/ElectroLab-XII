
import pytest

from electrolab.protocol import ArduinoSample
from electrolab.serial_reader import SerialEvent
from electrolab.arduino_processing import (
    ArduinoMeasurementProcessor,
)


def make_event(seq, uptime_ms, current_ma=450.0, continuous=True):
    sample = ArduinoSample(
        sequence=seq,
        uptime_ms=uptime_ms,
        bus_voltage_v=4.0,
        shunt_voltage_mv=45.0,
        current_ma=current_ma,
    )

    return SerialEvent(
        status="sample",
        sample=sample,
        continuous=continuous,
    )


def test_charge_integration():
    processor = ArduinoMeasurementProcessor()

    first = processor.process(
        make_event(0, 500, 450.0, False)
    )

    second = processor.process(
        make_event(1, 1000, 460.0)
    )

    assert first is not None
    assert second is not None

    assert first.charge_c == 0.0
    assert second.charge_c == pytest.approx(0.2275)
    assert second.copper_mg > 0


def test_packet_gap_not_integrated():
    processor = ArduinoMeasurementProcessor()

    processor.process(make_event(0, 500, continuous=False))
    processor.process(make_event(1, 1000))

    before = processor.total_charge_c

    processor.process(
        make_event(5, 3000, continuous=False)
    )

    assert processor.total_charge_c == pytest.approx(before)


def test_pause_and_resume():
    processor = ArduinoMeasurementProcessor()

    processor.process(make_event(0, 500, continuous=False))
    processor.process(make_event(1, 1000))

    before = processor.total_charge_c

    processor.pause()
    assert processor.process(make_event(2, 1500)) is None

    processor.resume()
    processor.process(make_event(3, 2000, continuous=False))

    assert processor.total_charge_c == pytest.approx(before)

    processor.process(make_event(4, 2500))

    assert processor.total_charge_c > before


