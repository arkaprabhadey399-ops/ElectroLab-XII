"""Arduino communication protocol for ElectroLab X."""

import json
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ArduinoSample:
    sequence: int
    uptime_ms: int
    bus_voltage_v: float
    shunt_voltage_mv: float
    current_ma: float


@dataclass(frozen=True)
class ArduinoError:
    uptime_ms: int
    code: str


def parse_packet(line: str) -> ArduinoSample | ArduinoError:
    """Parse and validate one Arduino JSON Lines packet."""

    if len(line) > 512:
        raise ValueError("Serial packet too long.")

    try:
        packet = json.loads(line)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON packet.") from exc

    if not isinstance(packet, dict):
        raise ValueError("Packet must be a JSON object.")

    if type(packet.get("version")) is not int:
        raise ValueError("Invalid protocol version.")

    if packet["version"] != 1:
        raise ValueError("Unsupported protocol version.")

    uptime = packet.get("uptime_ms")

    if (
        type(uptime) is not int
        or not 0 <= uptime <= 4294967295
    ):
        raise ValueError("Invalid Arduino timestamp.")

    kind = packet.get("kind")

    if kind == "error":
        code = packet.get("code")

        if not isinstance(code, str) or not code.strip():
            raise ValueError("Invalid sensor error code.")

        return ArduinoError(
            uptime_ms=uptime,
            code=code,
        )

    if kind != "sample":
        raise ValueError("Unknown packet kind.")

    sequence = packet.get("seq")

    if type(sequence) is not int or sequence < 0:
        raise ValueError("Invalid sequence number.")

    fields = (
        "bus_voltage_v",
        "shunt_voltage_mv",
        "current_ma",
    )

    values = {}

    for field in fields:
        value = packet.get(field)

        if (
            type(value) not in (int, float)
            or not math.isfinite(value)
        ):
            raise ValueError(f"Invalid measurement: {field}")

        values[field] = float(value)

    if values["bus_voltage_v"] < 0:
        raise ValueError("Negative bus voltage.")

    return ArduinoSample(
        sequence=sequence,
        uptime_ms=uptime,
        bus_voltage_v=values["bus_voltage_v"],
        shunt_voltage_mv=values["shunt_voltage_mv"],
        current_ma=values["current_ma"],
    )
