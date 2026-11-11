
import pytest
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

# Verify that the acquisition thread was created.
    assert acquisition._thread is not None

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


def test_invalid_queue_capacity():
    with pytest.raises(ValueError):
        NanoAcquisition(
            reader=FakeReader(),
            max_queue_size=0,
        )


def test_queue_overflow_is_reported():
    fake = FakeReader()

    # Supply enough events to overflow a two-event queue.
    fake.events = iter([
        SerialEvent(status="timeout")
        for _ in range(5)
    ])

    acquisition = NanoAcquisition(
        reader=fake,
        max_queue_size=2,
    )

    acquisition.start()
    assert acquisition._thread is not None
    acquisition._thread.join(timeout=2.0)

    events = acquisition.get_pending_events()

    assert len(events) == 1
    assert events[0].status == "overflow"
    assert acquisition.is_running is False
    assert fake.closed is True

