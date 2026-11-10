
"""Test ElectroLab X's reusable Arduino serial receiver."""

import time

from electrolab.serial_reader import NanoSerialReader


def main():
    reader = NanoSerialReader(
        port="COM3",
        baudrate=115200,
        timeout_s=2.0,
    )

    try:
        reader.connect()

        print("ElectroLab X - Arduino Connected!")
        print("Waiting for validated measurements...\n")

        # Allow Nano to restart after opening serial.
        time.sleep(2)

        while True:
            event = reader.read_event()

            if event.status == "sample":
                sample = event.sample

                if sample is None:
                    continue

                continuity = (
                    "CONTINUOUS"
                    if event.continuous
                    else "NEW BASELINE"
                )

                print(
                    f"Seq: {sample.sequence} | "
                    f"Time: {sample.uptime_ms / 1000:.2f}s | "
                    f"Voltage: {sample.bus_voltage_v:.3f}V | "
                    f"Current: {sample.current_ma:.2f}mA | "
                    f"{continuity} | ARDUINO MOCK"
                )

            elif event.status == "timeout":
                print("WARNING: Serial timeout.")

            elif event.status == "invalid":
                print(f"INVALID PACKET: {event.message}")

            elif event.status == "disconnected":
                print(f"DISCONNECTED: {event.message}")
                break

            elif event.status == "sensor_error":
                print(f"SENSOR ERROR: {event.message}")

    except KeyboardInterrupt:
        print("\nReceiver stopped by user.")

    finally:
        reader.close()
        print("Serial connection closed.")


if __name__ == "__main__":
    main()


