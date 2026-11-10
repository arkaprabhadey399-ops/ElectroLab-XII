
"""USB serial communication test for ElectroLab X."""

import json
import time
import serial

from electrolab.protocol import (
    ArduinoSample,
    ArduinoError,
    parse_packet,
)

PORT = "COM3"
BAUD_RATE = 115200


def main():
    try:
        with serial.Serial(
            PORT,
            BAUD_RATE,
            timeout=2,
        ) as connection:

            # Opening the port may reset the Nano.
            time.sleep(2)

            print("Connected to Arduino Nano!")
            print("Waiting for synthetic measurements...")
            print("Press Ctrl+C to stop.\n")

            while True:
                raw = connection.readline()

                if not raw:
                    print("No data received (timeout).")
                    continue

                try:
                    line = raw.decode("utf-8").strip()
                    packet_json = json.loads(line)

                    if not isinstance(packet_json, dict):
                        raise ValueError("Expected a JSON object.")

                    # This demonstration accepts MOCK packets only.
                    if (
                        packet_json.get("source") != "ARDUINO_MOCK"
                        or packet_json.get("simulated") is not True
                    ):
                        raise ValueError(
                            "Packet is not explicitly marked as mock."
                        )

                    packet = parse_packet(line)

                    if isinstance(packet, ArduinoError):
                        print(f"Sensor error: {packet.code}")
                        continue

                    if isinstance(packet, ArduinoSample):
                        print(
                            f"Time: {packet.uptime_ms / 1000:.1f}s | "
                            f"Voltage: {packet.bus_voltage_v:.3f}V | "
                            f"Current: {packet.current_ma:.2f}mA "
                            "[ARDUINO MOCK]"
                        )

                except (UnicodeDecodeError, ValueError) as exc:
                    print(f"Invalid packet: {exc}")

    except (serial.SerialException, OSError) as exc:
        print(f"Serial connection error: {exc}")

    except KeyboardInterrupt:
        print("\nSerial receiver stopped.")


if __name__ == "__main__":
    main()
