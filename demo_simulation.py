from electrolab.simulation import ElectroplatingSimulator
from electrolab.experiment import ChargeIntegrator

simulator = ElectroplatingSimulator()
integrator = ChargeIntegrator()
integrator.start()

print("Time(s) | Voltage(V) | Current(mA) | Charge(C) | Copper(mg)")
print("-" * 70)

for _ in range(20):
    sample = simulator.next_measurement()

    charge = integrator.add_measurement(
        sample.timestamp_s,
        sample.current_a,
    )

    print(
        f"{sample.timestamp_s:7.2f} | "
        f"{sample.voltage_v:10.3f} | "
        f"{sample.current_a * 1000:11.2f} | "
        f"{charge:9.4f} | "
        f"{integrator.theoretical_mass_mg:10.4f}"
    )

