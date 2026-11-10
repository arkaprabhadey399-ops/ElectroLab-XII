
"""Independent Arduino data acquisition for ElectroLab X."""

from queue import Empty, Queue
from threading import Event, Thread

from electrolab.serial_reader import (
    NanoSerialReader,
    SerialEvent,
)


class NanoAcquisition:
    """Receive Arduino mock packets independently of Streamlit."""

    def __init__(
        self,
        port: str = "COM3",
        reader: NanoSerialReader | None = None,
    ):
        self.reader = reader or NanoSerialReader(
            port=port,
            baudrate=115200,
            timeout_s=0.5,
        )

        self.events: Queue[SerialEvent] = Queue()
        self._stop_event = Event()
        self._thread: Thread | None = None

    def start(self):
        """Start a background acquisition thread."""
        if self._thread is not None:
            raise RuntimeError(
                "Create a new acquisition object for a new session."
            )

        self._stop_event.clear()

        self._thread = Thread(
            target=self._run,
            daemon=True,
            name="ElectroLab-Nano-Acquisition",
        )

        self._thread.start()

    def _run(self):
        """Read serial events in the background."""
        try:
            self.reader.connect()

            while not self._stop_event.is_set():
                event = self.reader.read_event()

                self.events.put(event)

                if event.status == "disconnected":
                    break

        except (OSError, RuntimeError) as exc:
            self.events.put(
                SerialEvent(
                    status="disconnected",
                    message=str(exc),
                )
            )

        finally:
            self.reader.close()

    def get_pending_events(
        self,
        limit: int = 100,
    ) -> list[SerialEvent]:
        """Collect pending events without blocking the dashboard."""
        if limit <= 0:
            raise ValueError("Limit must be positive.")

        result = []

        for _ in range(limit):
            try:
                result.append(self.events.get_nowait())
            except Empty:
                break

        return result

    def stop(self):
        """Request acquisition shutdown."""
        self._stop_event.set()

        if self._thread is not None:
            self._thread.join(timeout=3.0)

            if self._thread.is_alive():
                raise RuntimeError(
                    "Acquisition thread did not stop cleanly."
                )

    @property
    def is_running(self) -> bool:
        return (
            self._thread is not None
            and self._thread.is_alive()
            and not self._stop_event.is_set()
        )


