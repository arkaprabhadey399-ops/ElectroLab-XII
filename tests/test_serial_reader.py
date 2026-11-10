
import json

from electrolab.serial_reader import NanoSerialReader


class FakeSerial:
    """Simulate a serial port for automated testing."""

    def __init__(self, lines):
        self.lines = iter(lines)
        self.closed = False

    def readline(self):
        return next(self.lines, b"")

    def close(self):
        self.closed = True


def mock_packet(seq, uptime_ms):
    return (
        json.dumps({
            "version": 1,
            "kind": "sample",
            "seq": seq,
            "uptime_ms": uptime_ms,
            "bus_voltage_v": 4.0,
            "shunt_voltage_mv": 45.0,
            "current_ma": 450.0,
            "source": "ARDUINO_MOCK",
            "simulated": True,
        }) + "\n"
    ).encode("utf-8")


def test_consecutive_packets():
    fake = FakeSerial([
        mock_packet(0, 500),
        mock_packet(1, 1000),
    ])

    reader = NanoSerialReader(connection=fake)

    first = reader.read_event()
    second = reader.read_event()

    assert first.status == "sample"
    assert first.continuous is False

    assert second.status == "sample"
    assert second.continuous is True


def test_missing_packet_breaks_continuity():
    fake = FakeSerial([
        mock_packet(0, 500),
        mock_packet(3, 2000),
    ])

    reader = NanoSerialReader(connection=fake)

    reader.read_event()
    second = reader.read_event()

    assert second.status == "sample"
    assert second.continuous is False


def test_invalid_packet():
    fake = FakeSerial([b"not valid json\n"])

    reader = NanoSerialReader(connection=fake)

    event = reader.read_event()

    assert event.status == "invalid"


def test_timeout_breaks_continuity():
    fake = FakeSerial([
        mock_packet(0, 500),
        b"",
        mock_packet(1, 1000),
    ])

    reader = NanoSerialReader(connection=fake)

    reader.read_event()
    timeout = reader.read_event()
    resumed = reader.read_event()

    assert timeout.status == "timeout"
    assert resumed.continuous is False
