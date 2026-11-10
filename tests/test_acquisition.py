
from electrolab.acquisition import NanoAcquisition
from electrolab.serial_reader import SerialEvent


class FakeReader:
    """Mock receiver that does not require an Arduino."""

    def __init__(self):
        self.connected = False
        self.closed = False
        self.events = iter([
            SerialEvent(status="timeout"),
            SerialEvent(
                status="disconnected",
                message="Mock disconnection",
            ),
        ])

    def connect(self):
        self.connected = True

    def read_event(self):
        return next(self.events)

    def close(self):
        self.closed = True


def test_background_acquisition():
    fake = FakeReader()
    acquisition = NanoAcquisition(reader=fake)

    acquisition.start()
    acquisition._thread.join(timeout=2.0)

    events = acquisition.get_pending_events()

    assert fake.connected is True
    assert fake.closed is True

    assert [event.status for event in events] == [
        "timeout",
        "disconnected",
    ]


def test_empty_queue():
    acquisition = NanoAcquisition(reader=FakeReader())

    assert acquisition.get_pending_events() == []


def test_invalid_queue_limit():
    acquisition = NanoAcquisition(reader=FakeReader())

    try:
        acquisition.get_pending_events(limit=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")

