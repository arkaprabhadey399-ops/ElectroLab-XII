
"""Convert Arduino mock packets into ElectroLab X records."""

from electrolab.arduino_processing import ArduinoMeasurementProcessor
from electrolab.serial_reader import SerialEvent


class ArduinoMockBridge:
    """Prepare validated Arduino mock data for the dashboard."""

    def __init__(self):
        self.processor = ArduinoMeasurementProcessor()
        self._first_uptime_ms: int | None = None
        self._previous_uptime_ms: int | None = None
        self._segment_start_s: float = 0.0
        self._last_time_s: float | None = None

    def pause(self):
        self.processor.pause()
        self._first_uptime_ms = None
        self._previous_uptime_ms = None

    def resume(self):
        self.processor.resume()
        self._first_uptime_ms = None
        self._previous_uptime_ms = None

    def reset(self):
        self.processor.reset()
        self._first_uptime_ms = None
        self._previous_uptime_ms = None
        self._segment_start_s = 0.0
        self._last_time_s = None

    def consume(self, event: SerialEvent) -> dict | None:
        """Convert one serial event into a dashboard record."""

        processed = self.processor.process(event)

        if processed is None or event.sample is None:
            return None

        raw = event.sample

        # A new segment begins after resume or an Arduino restart.
        new_segment = (
            self._first_uptime_ms is None
            or (
                self._previous_uptime_ms is not None
                and raw.uptime_ms <= self._previous_uptime_ms
            )
        )

        if new_segment:
            self._first_uptime_ms = raw.uptime_ms
            self._segment_start_s = (
                0.0
                if self._last_time_s is None
                else self._last_time_s + 0.5
            )

        
        # The baseline must be initialized before subtraction.
        assert self._first_uptime_ms is not None

        time_s = (
            self._segment_start_s
            + (raw.uptime_ms - self._first_uptime_ms) / 1000.0
        )


        self._previous_uptime_ms = raw.uptime_ms
        self._last_time_s = time_s

        return {
            "time_s": time_s,
            "voltage_v": processed.bus_voltage_v,
            "current_ma": processed.current_ma,
            "power_w": processed.bus_power_w,
            "charge_c": processed.charge_c,
            "copper_mg": processed.copper_mg,
            "source": "ARDUINO_MOCK",
        }

