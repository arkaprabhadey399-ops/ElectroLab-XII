
"""Independent Arduino data acquisition for ElectroLab X."""

from typing import Protocol
from queue import Empty, Full, Queue
from threading import Event, Thread

from electrolab.serial_reader import (
    NanoSerialReader,
    SerialEvent,
)

class SerialReaderProtocol(Protocol):
    """Methods required by the acquisition system."""

    def connect(self) -> None:
        ...

    def read_event(self) -> SerialEvent:
        ...

    def close(self) -> None:
        ...

class NanoAcquisition:
    """Receive Arduino mock packets independently of Streamlit."""

    def __init__(
        self,
        port: str = "COM3",
        reader: SerialReaderProtocol | None = None,
        max_queue_size: int = 200,
    ):
        self.reader: SerialReaderProtocol = (
            reader
            if reader is not None
            else NanoSerialReader(
                port=port,
                baudrate=115200,
                timeout_s=1.5,
            )
        )


        if max_queue_size <= 0:
            raise ValueError("Queue capacity must be positive.")

        self.events: Queue[SerialEvent] = Queue(
            maxsize=max_queue_size
        ) 

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

    def _put_event(self, event: SerialEvent) -> bool:
        """Queue an event, or stop safely if the buffer overflows."""

        try:
            self.events.put_nowait(event)
            return True

        except Full:
            # Some packets have not been processed.
            # Stop acquisition and report data loss.
            self._stop_event.set()

            # Discard the unprocessed backlog so the
            # dashboard cannot integrate across missing data.
            while True:
                try:
                    self.events.get_nowait()
                except Empty:
                    break

            self.events.put_nowait(
                SerialEvent(
                    status="overflow",
                    message=(
                        "Acquisition buffer overflow. "
                        "Unprocessed measurements were discarded."
                    ),
                )
            )

            return False

    def _run(self):
        """Read serial events in the background.""" 
        try:
            self.reader.connect()

            while not self._stop_event.is_set():
                event = self.reader.read_event()

                if not self._put_event(event):
                    break

                if event.status == "disconnected":
                    break

        except (OSError, RuntimeError) as exc:
            self._put_event(
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


