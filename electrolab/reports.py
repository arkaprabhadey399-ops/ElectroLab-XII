
"""Scientific experiment report generation for ElectroLab X."""

import math
from statistics import mean

from electrolab.calculations import (
    actual_mass_gain,
    current_efficiency,
    theoretical_copper_mass,
)


def generate_experiment_report(
    history: list[dict],
    experiment_name: str,
    area_cm2: float,
    initial_mass_g: float | None = None,
    final_mass_g: float | None = None,
) -> str:
    """Generate a scientific summary from recorded measurements."""

    if not history:
        raise ValueError("Cannot generate a report without measurements.")

    if not experiment_name.strip():
        raise ValueError("Experiment name cannot be empty.")

    if not math.isfinite(area_cm2) or area_cm2 <= 0:
        raise ValueError("Cathode area must be positive and finite.")

    required = (
        "time_s", "voltage_v", "current_ma",
        "power_w", "charge_c", "source",
    )

    for index, record in enumerate(history):
        missing = set(required) - set(record)

        if missing:
            raise ValueError(
                f"Record {index} is missing: {sorted(missing)}"
            )

        for field in required[:-1]:
            try:
                valid = math.isfinite(record[field])
            except (TypeError, ValueError):
                valid = False

            if not valid:
                raise ValueError(
                    f"Invalid {field} in record {index}"
                )

    times = [row["time_s"] for row in history]

    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Measurement timestamps must increase.")

    voltages = [row["voltage_v"] for row in history]
    currents = [row["current_ma"] for row in history]
    powers = [row["power_w"] for row in history]

    charge_c = history[-1]["charge_c"]

    if charge_c < 0:
        raise ValueError("Accumulated charge cannot be negative.")

    theoretical_g = theoretical_copper_mass(charge_c)
    theoretical_mg = theoretical_g * 1000

    sources = ", ".join(
        sorted({str(row["source"]) for row in history})
    )

    report = [
        "ELECTROLAB X — SCIENTIFIC EXPERIMENT REPORT",
        "=" * 52,
        "",
        f"Experiment: {experiment_name}",
        f"Data source: {sources}",
        f"Recorded samples: {len(history)}",
        f"Recorded time span: {times[-1] - times[0]:.2f} s",
        f"Cathode exposed area: {area_cm2:.2f} cm²",
        "",
        "ELECTRICAL ANALYSIS",
        "-" * 30,
        f"Mean sampled voltage: {mean(voltages):.4f} V",
        f"Mean sampled current: {mean(currents):.4f} mA",
        f"Mean sampled power: {mean(powers):.4f} W",
        f"Integrated charge: {charge_c:.6f} C",
        "",
        "ELECTROCHEMICAL ANALYSIS",
        "-" * 30,
        f"Theoretical copper deposit: {theoretical_mg:.6f} mg",
        "Copper molar mass: 63.546 g/mol",
        "Electron stoichiometry: 2 electrons per Cu ion",
        "Faraday constant: 96485 C/mol",
        "",
    ]

    if initial_mass_g is not None and final_mass_g is not None:
        gain_g = actual_mass_gain(initial_mass_g, final_mass_g)

        report.extend([
            f"Entered initial mass: {initial_mass_g:.6f} g",
            f"Entered final mass: {final_mass_g:.6f} g",
            f"Entered mass gain: {gain_g * 1000:.6f} mg",
        ])

        if gain_g >= 0 and theoretical_g > 0:
            efficiency = current_efficiency(
                gain_g, theoretical_g
            )
            report.append(
                f"Apparent current efficiency: {efficiency:.2f}%"
            )
        else:
            report.append(
                "Current efficiency: Not interpretable"
            )
    else:
        report.append(
            "Mass comparison: Not available (missing balance readings)"
        )

    report.extend([
        "",
        "SCIENTIFIC LIMITATIONS",
        "-" * 30,
        "1. Theoretical mass assumes Cu2+ + 2e- -> Cu.",
        "2. Charge excludes unrecorded and paused intervals.",
        "3. Sample means are arithmetic, not time-weighted.",
        "4. Entered masses require independent balance verification.",
        "5. SIMULATION data are synthetic, not physical measurements.",
        "6. Actual cell voltage requires verified sensor placement.",
        "",
        "End of ElectroLab X report.",
    ])

    return "\n".join(report) + "\n"
