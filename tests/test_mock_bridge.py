
import pytest

from electrolab.mock_bridge import ArduinoMockBridge
from electrolab.protocol import ArduinoSample
from electrolab.serial_reader import SerialEvent


def make_event(seq, uptime_ms, continuous):
    return SerialEvent(
        status="sample",
        sample=ArduinoSample(
            sequence=seq,
            uptime_ms=uptime_ms,
            bus_voltage_v=4.0,
            shunt_voltage_mv=45.0,
            current_ma=450.0,
        ),
        continuous=continuous,
    )


def test_bridge_generates_dashboard_records():
    bridge = ArduinoMockBridge()

    first = bridge.consume(make_event(0, 500, False))
    second = bridge.consume(make_event(1, 1000, True))

    assert first is not None
    assert second is not None

    assert first["charge_c"] == pytest.approx(0.0)
    assert second["charge_c"] == pytest.approx(0.225)
    assert second["time_s"] == pytest.approx(0.5)
    assert second["source"] == "ARDUINO_MOCK"


def test_bridge_preserves_charge_after_pause():
    bridge = ArduinoMockBridge()

    bridge.consume(make_event(0, 500, False))
    before = bridge.consume(make_event(1, 1000, True))

    assert before is not None

    bridge.pause()
    assert bridge.consume(make_event(2, 1500, True)) is None

    bridge.resume()

    resumed = bridge.consume(make_event(0, 500, False))

    assert resumed is not None
    assert resumed["charge_c"] == pytest.approx(
        before["charge_c"]
    )
    assert resumed["time_s"] > before["time_s"]
