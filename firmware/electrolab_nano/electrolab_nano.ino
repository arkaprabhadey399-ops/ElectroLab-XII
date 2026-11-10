
/*
 * ElectroLab X — Arduino Nano
 * Firmware Stage 1: MOCK SERIAL MEASUREMENTS
 *
 * No INA219 sensor required.
 * All measurements are synthetic.
 */

#include <Arduino.h>
#include <math.h>

const unsigned long SAMPLE_INTERVAL_MS = 500;

unsigned long lastSampleMs = 0;
unsigned long sequenceNumber = 0;

void setup() {
    Serial.begin(115200);

    pinMode(LED_BUILTIN, OUTPUT);
}

void loop() {
    unsigned long now = millis();

    if (now - lastSampleMs < SAMPLE_INTERVAL_MS) {
        return;
    }

    lastSampleMs = now;

    // Time since Arduino startup in seconds.
    float t = now / 1000.0f;

    // Synthetic electrical measurements.
    float voltage = 4.0f + 0.04f * sin(t * 0.2f);
    float current = 450.0f + 15.0f * sin(t * 0.5f);

    // Illustrative 0.1-ohm shunt calculation.
    float shuntVoltage = current * 0.1f;

    // Transmit one JSON packet per line.
    Serial.print(F("{\"version\":1,\"kind\":\"sample\",\"seq\":"));
    Serial.print(sequenceNumber++);

    Serial.print(F(",\"uptime_ms\":"));
    Serial.print(now);

    Serial.print(F(",\"bus_voltage_v\":"));
    Serial.print(voltage, 3);

    Serial.print(F(",\"shunt_voltage_mv\":"));
    Serial.print(shuntVoltage, 3);

    Serial.print(F(",\"current_ma\":"));
    Serial.print(current, 2);

    Serial.println(
        F(",\"source\":\"ARDUINO_MOCK\",\"simulated\":true}")
    );

    digitalWrite(
        LED_BUILTIN,
        !digitalRead(LED_BUILTIN)
    );
}

