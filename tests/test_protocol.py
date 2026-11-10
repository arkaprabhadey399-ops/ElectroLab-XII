import pytest

from electrolab.protocol import (
    ArduinoSample,
    ArduinoError,
    parse_packet,
)


def test_valid_measurement_packet():
    line = (
        '{"version":1,"kind":"sample","seq":1,'
        '"uptime_ms":1000,"bus_voltage_v":4.02,'
        '"shunt_voltage_mv":4.5,"current_ma":450.0}'
    )

    result = parse_packet(line)

    assert isinstance(result, ArduinoSample)
    assert result.current_ma == pytest.approx(450.0)
    assert result.bus_voltage_v == pytest.approx(4.02)
    assert result.uptime_ms == 1000


def test_sensor_error_packet():
    line = (
        '{"version":1,"kind":"error",'
        '"uptime_ms":1500,'
        '"code":"INA219_NOT_FOUND"}'
    )

    result = parse_packet(line)

    assert isinstance(result, ArduinoError)
    assert result.code == "INA219_NOT_FOUND"


def test_malformed_json():
    with pytest.raises(ValueError):
        parse_packet('{"version":1,"kind":')


def test_invalid_sensor_reading():
    line = (
        '{"version":1,"kind":"sample","seq":2,'
        '"uptime_ms":2000,"bus_voltage_v":4.0,'
        '"shunt_voltage_mv":2.0,"current_ma":NaN}'
    )

    with pytest.raises(ValueError):
        parse_packet(line)
