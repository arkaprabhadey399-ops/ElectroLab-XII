
"""Validated USB serial receiver for ElectroLab X."""

import json
from dataclasses import dataclass

import serial

from electrolab.protocol import (
    ArduinoSample,
    ArduinoError,
    parse_packet,
)


@dataclass(frozen=True)
class SerialEvent:
    status: str
    sample: ArduinoSample | None = None
    continuous: bool = False
    message: str = ""


class NanoSerialReader:
    """Read and validate Arduino mock measurements."""

    def __init__(
        self,
        port: str = "COM3",
        baudrate: int = 115200,
        timeout_s: float = 2.0,
        connection=None,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout_s = timeout_s
        self.connection = connection

        self.previous_sequence = None
        self.previous_uptime = None

    def connect(self):
        """Open the Arduino serial port."""
        if self.connection is None:
            self.connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout_s,
            )

        self._break_continuity()

    def _break_continuity(self):
        self.previous_sequence = None
        self.previous_uptime = None

    def read_event(self) -> SerialEvent:
        """Read one packet and return a validated event."""

        if self.connection is None:
            raise RuntimeError("Serial connection is not open.")

        try:
            raw = self.connection.readline()
        except (serial.SerialException, OSError) as exc:
            self._break_continuity()
            self.close()
            return SerialEvent("disconnected", message=str(exc))

        if not raw:
            self._break_continuity()
            return SerialEvent("timeout", message="No packet received.")

        try:
            line = raw.decode("utf-8").strip()
            envelope = json.loads(line)

            if not isinstance(envelope, dict):
                raise ValueError("Expected a JSON object.")

            packet = parse_packet(line)

            if isinstance(packet, ArduinoError):
                self._break_continuity()
                return SerialEvent(
                    "sensor_error",
                    message=packet.code,
                )

            # This receiver accepts only mock data.
            if (
                envelope.get("source") != "ARDUINO_MOCK"
                or envelope.get("simulated") is not True
            ):
                raise ValueError(
                    "Packet must be explicitly marked ARDUINO_MOCK."
                )

            continuous = (
                self.previous_sequence is not None
                and packet.sequence == self.previous_sequence + 1
                and packet.uptime_ms > self.previous_uptime
            )

            self.previous_sequence = packet.sequence
            self.previous_uptime = packet.uptime_ms

            return SerialEvent(
                status="sample",
                sample=packet,
                continuous=continuous,
            )

        except (UnicodeDecodeError, ValueError) as exc:
            self._break_continuity()
            return SerialEvent("invalid", message=str(exc))

    def close(self):
        """Close the serial port safely."""
        if self.connection is not None:
            self.connection.close()
            self.connection = None

        self._break_continuity()
