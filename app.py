
import pandas as pd
import streamlit as st


from electrolab.acquisition import NanoAcquisition
from electrolab.mock_bridge import ArduinoMockBridge


from electrolab.calculations import (
    current_density,
    actual_mass_gain,
    current_efficiency,
)
from electrolab.simulation import ElectroplatingSimulator
from electrolab.experiment import ChargeIntegrator
from electrolab.charts import (
    make_time_series_chart,
    make_deposition_comparison_chart,
)
from electrolab.storage import (
    measurements_to_csv,
    create_experiment_log,
    append_measurement,
)
from electrolab.reports import generate_experiment_report

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="ElectroLab X",
    page_icon="⚡",
    layout="wide",
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "simulator" not in st.session_state:
    st.session_state.simulator = ElectroplatingSimulator()

if "integrator" not in st.session_state:
    st.session_state.integrator = ChargeIntegrator()

if "latest_sample" not in st.session_state:
    st.session_state.latest_sample = None

if "running" not in st.session_state:
    st.session_state.running = False

if "history" not in st.session_state:
    st.session_state.history = []

if "previous_mode" not in st.session_state:
    st.session_state.previous_mode = "Simulation Mode"

if "log_path" not in st.session_state:
    st.session_state.log_path = None

if "log_error" not in st.session_state:
    st.session_state.log_error = None

if "stopped" not in st.session_state:
    st.session_state.stopped = False

if "mock_bridge" not in st.session_state:
    st.session_state.mock_bridge = ArduinoMockBridge()

if "nano_acquisition" not in st.session_state:
    st.session_state.nano_acquisition = None


def release_nano_acquisition():
    """Stop Arduino acquisition and release the serial port."""

    acquisition = st.session_state.nano_acquisition

    if acquisition is not None:
        acquisition.stop()
        st.session_state.nano_acquisition = None


def reset_experiment():

    # Stop any active Arduino communication.
    release_nano_acquisition()

    # Reset Arduino scientific processing.
    st.session_state.mock_bridge.reset()

    """Reset simulation and measurement history."""
    st.session_state.simulator = ElectroplatingSimulator()
    st.session_state.integrator = ChargeIntegrator()
    st.session_state.latest_sample = None
    st.session_state.history = []
    st.session_state.running = False
    st.session_state.log_path = None
    st.session_state.log_error = None
    st.session_state.stopped = False
    st.session_state.pop("initial_mass_g", None)
    st.session_state.pop("final_mass_g", None)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("⚡ ElectroLab X")

st.caption(
    "Advanced Electrochemical Monitoring & Analysis System"
)

st.divider()


def start_or_resume():
    """Start or resume the selected experiment mode."""

    if st.session_state.running or st.session_state.stopped:
        return

    selected_mode = st.session_state.measurement_mode

    port: str = ""


    # Physical sensor integration is not yet verified.
    if selected_mode == "Live Arduino Mode":
        st.session_state.log_error = (
            "Live INA219 mode is not enabled."
        )
        return

    if selected_mode == "Arduino Mock Mode":
        port = st.session_state.serial_port.strip()

        if not port:
            st.session_state.log_error = (
                "Enter a valid Arduino COM port."
            )
            return

    # Create an experiment log if this is a new session.
    if st.session_state.log_path is None:
        try:
            st.session_state.log_path = create_experiment_log()
        except OSError as exc:
            st.session_state.log_error = str(exc)
            return

    st.session_state.log_error = None

    if selected_mode == "Simulation Mode":
        st.session_state.integrator.start()

    elif selected_mode == "Arduino Mock Mode":
        st.session_state.mock_bridge.resume()

        acquisition = NanoAcquisition(
            port=port, 
        )

        try:
            acquisition.start()
        except RuntimeError as exc:
            st.session_state.mock_bridge.pause()
            st.session_state.log_error = str(exc)
            return

        st.session_state.nano_acquisition = acquisition

    st.session_state.running = True




def pause_experiment():
    """Pause the active software measurement session."""

    selected_mode = st.session_state.measurement_mode

    if selected_mode == "Simulation Mode":
        st.session_state.integrator.pause()

    elif selected_mode == "Arduino Mock Mode":
        release_nano_acquisition()
        st.session_state.mock_bridge.pause()

    st.session_state.running = False




def stop_experiment():
    """Finalize the current software experiment."""

    pause_experiment()
    st.session_state.stopped = True



# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:

    st.header("⚙️ Experiment Setup")

    experiment_name = st.text_input(
        "Experiment Name",
        value="Copper Electroplating Experiment",
    )

    mode = st.selectbox(
        "Measurement Mode",
        [
            "Simulation Mode",
            "Arduino Mock Mode",
            "Live Arduino Mode",
        ],
        key="measurement_mode",
        disabled=(
            st.session_state.running
            or bool(st.session_state.history)
        ),
    )

    serial_port = st.text_input(
        "Arduino Serial Port",
        value="COM3",
        disabled=mode != "Arduino Mock Mode",
        help="Example: COM3. Check Device Manager for your Nano's port.",
        key="serial_port",
    )

    if mode == "Arduino Mock Mode":
        st.caption(
            "Arduino-generated synthetic measurements. "
            "No physical sensor readings."
        )

    elif mode == "Live Arduino Mode":
        st.warning(
            "Live INA219 mode is not yet verified or enabled."  
        )
    exposed_area_cm2 = st.number_input(
        "Exposed Cathode Surface Area (cm²)",
        min_value=0.1,
        value=10.0,
        step=0.5,
        format="%.2f",
    )
    st.divider()
    st.subheader("Cathode Mass Measurements")

    initial_mass_g = st.number_input(
        "Initial Cathode Mass (g)",
        min_value=0.0,
        value=None,
        step=0.001,
        format="%.3f",
        placeholder="Enter initial mass",
        key="initial_mass_g",
    )

    final_mass_g = st.number_input(
        "Final Cathode Mass (g)",
        min_value=0.0,
        value=None,
        step=0.001,
        format="%.3f",
        placeholder="Enter final mass",
        key="final_mass_g",
        disabled=not st.session_state.stopped,
    )

    st.caption(
        "Measure the initial mass before plating. "
        "Enter the final mass after stopping the experiment, "
        "rinsing and thoroughly drying the cathode."
    )
    st.selectbox(
    "Graph Category",
    [
        "Electrical Measurements",
        "Power and Charge",
        "Copper Deposition",
    ],
    key="graph_view",
    )

    if mode != st.session_state.previous_mode:
        st.session_state.integrator.pause()
        st.session_state.running = False
        st.session_state.previous_mode = mode

    st.divider()

    
    # START / RESUME
    
    st.button(
        "▶ Start / Resume",
        on_click=start_or_resume,
        
        disabled=(
            mode == "Live Arduino Mode"
            or st.session_state.running
            or st.session_state.stopped
        ),

        use_container_width=True,
    )

    st.button(
        "⏸ Pause",
        on_click=pause_experiment,
        disabled=not st.session_state.running,
        use_container_width=True,
    )

    st.button(
        "⏹ Stop Experiment",
        on_click=stop_experiment,
        disabled=(
            st.session_state.stopped
            or not st.session_state.history
        ),
        use_container_width=True,
    )

    st.button(
        "↺ Reset Experiment",
        on_click=reset_experiment,
        use_container_width=True,
    )



    st.divider()
    st.caption("ElectroLab X | Version 0.3")


# --------------------------------------------------
# LIVE DASHBOARD
# --------------------------------------------------

refresh_interval = (
    "500ms"
    if mode == "Simulation Mode" and st.session_state.running
    else None
)


@st.fragment(run_every=refresh_interval)
def live_dashboard():

    if mode != "Simulation Mode":
        st.warning(
            "Live Arduino acquisition is not available yet. "
            "Hardware integration requires electrical verification."
        )
        return

    # Generate one measurement while running
    if st.session_state.running:

        sample = st.session_state.simulator.next_measurement()

        charge = st.session_state.integrator.add_measurement(
            sample.timestamp_s,
            sample.current_a,
        )

        st.session_state.latest_sample = sample

                # Create a measurement record.
        measurement = {
            "time_s": sample.timestamp_s,
            "voltage_v": sample.voltage_v,
            "current_ma": sample.current_a * 1000,
            "power_w": sample.power_w,
            "charge_c": charge,
            "copper_mg": st.session_state.integrator.theoretical_mass_mg
                if False else st.session_state.integrator.theoretical_mass_mg,
            "source": sample.source,
        }

        # Preserve the measurement in memory.
        st.session_state.history.append(measurement)

        # Save the measurement to disk.
        try:
            if st.session_state.log_path is None:
                raise OSError("No active experiment log.")

            append_measurement(
                st.session_state.log_path,
                measurement,
            )

        except (OSError, ValueError) as exc:
            st.session_state.log_error = str(exc)
            st.session_state.integrator.pause()
            st.session_state.running = False
            st.session_state.stopped = True

    sample = st.session_state.latest_sample
    integrator = st.session_state.integrator

    if st.session_state.running:
        st.success("● SIMULATION RUNNING")
    else:
        st.info("● SIMULATION PAUSED / NOT STARTED")
    if st.session_state.log_path is not None:
        st.caption(
            "Automatic logging: "
            f"{st.session_state.log_path.name}"
        )

    if st.session_state.log_error:
        st.error(
            "Logging error: "
            f"{st.session_state.log_error}"
        )

    if sample is None:
        st.info("No measurements yet. Press Start / Resume.")
        return

    # --------------------------------------------------
    # LIVE INSTRUMENTS
    # --------------------------------------------------

    st.subheader("Live Electrical Measurements")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Voltage",
        f"{sample.voltage_v:.3f} V",
    )

    col2.metric(
        "Current",
        f"{sample.current_a * 1000:.2f} mA",
    )

    col3.metric(
        "Power",
        f"{sample.power_w:.3f} W",
    )

    col4.metric(
        "Accumulated Charge",
        f"{integrator.total_charge_c:.4f} C",
    )

    st.divider()

    st.subheader("Electrochemical Analysis")

    col1, col2 = st.columns(2)

    col1.metric(
        "Theoretical Copper Deposit",
        f"{integrator.theoretical_mass_mg:.4f} mg",
    )

    col2.metric(
        "Simulation Time",
        f"{sample.timestamp_s:.1f} s",
    )
    
    # Calculate current density
    density = current_density(
        sample.current_a,
        exposed_area_cm2,
    )

    st.metric(
        "Current Density",
        f"{density * 100:.3f} A/dm²",
    )

    st.caption(
        f"Equivalent to {density:.5f} A/cm²"
    )


    st.divider()
    st.subheader("Experimental Deposition Analysis")

    if not st.session_state.stopped:
        st.info(
            "Stop the experiment and enter the final "
            "cathode mass to calculate current efficiency."
        )

    elif initial_mass_g is None or final_mass_g is None:
        st.info(
            "Enter both initial and final cathode masses "
            "to compare actual and theoretical deposition."
        )

    elif integrator.total_charge_c <= 0:
        st.warning(
            "Current efficiency cannot be calculated "
            "without positive accumulated charge."
        )

    else:
        actual_gain_g = actual_mass_gain(
            initial_mass_g,
            final_mass_g,
        )

        theoretical_gain_g = integrator.theoretical_mass_g

        if actual_gain_g < 0:
            st.warning(
                "The cathode has lost mass. This result "
                "cannot be interpreted as normal copper "
                "deposition efficiency."
            )

        else:
            efficiency_pct = current_efficiency(
                actual_gain_g,
                theoretical_gain_g,
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Actual Mass Gain",
                f"{actual_gain_g * 1000:.3f} mg",
            )

            col2.metric(
                "Theoretical Mass Gain",
                f"{theoretical_gain_g * 1000:.3f} mg",
            )

            col3.metric(
                "Apparent Current Efficiency",
                f"{efficiency_pct:.2f}%",
            )

            if efficiency_pct > 100:
                st.warning(
                    "Efficiency exceeds 100%. Check "
                    "mass measurements, drying, and "
                    "current measurement accuracy."
                )

            if mode == "Simulation Mode":
                st.caption(
                    "Illustrative comparison: theoretical "
                    "mass is calculated from simulated charge. "
                    "Mass values are manually entered."
                )

    # --------------------------------------------------
    # MEASUREMENT HISTORY
    # --------------------------------------------------

    df = pd.DataFrame(st.session_state.history)

    
    st.subheader("Live Experimental Graphs")

    graph_configs = {
        "Electrical Measurements": [
            ("current_ma", "Current vs Time", "Current (mA)", "#17B8A6"),
            ("voltage_v", "Voltage vs Time", "Voltage (V)", "#F59E0B"),
        ],
        "Power and Charge": [
            ("power_w", "Power vs Time", "Power (W)", "#A78BFA"),
            ("charge_c", "Charge vs Time", "Charge (C)", "#38BDF8"),
        ],
        "Copper Deposition": [
            ("copper_mg", "Copper Deposition vs Time",
             "Copper Mass (mg)", "#FB923C"),
        ],
    }

    graph_view = st.session_state["graph_view"]
    st.caption(f"Currently displaying: {graph_view}")

    selected_graphs = graph_configs[graph_view]
    columns = st.columns(len(selected_graphs))

    for column, (y_col, title, y_label, color) in zip(
        columns, selected_graphs
    ):
        with column:
            fig = make_time_series_chart(
                data=df,
                y_column=y_col,
                title=title,
                y_label=y_label,
                color=color,
            )

            st.plotly_chart(
                fig,
                width="stretch",
                key=f"graph_{y_col}",
            )

    st.caption(
        f"{len(df)} simulated measurements recorded. "
        "All values are synthetic."
    )

    # Sixth graph: final measured/entered mass comparison.
    if (
        st.session_state["graph_view"] == "Copper Deposition"
        and st.session_state.stopped
        and initial_mass_g is not None
        and final_mass_g is not None
        and integrator.total_charge_c > 0
    ):
        actual_gain_g = actual_mass_gain(
            initial_mass_g,
            final_mass_g,
        )

        if actual_gain_g >= 0:
            comparison_fig = make_deposition_comparison_chart(
                theoretical_mg=integrator.theoretical_mass_mg,
                actual_mg=actual_gain_g * 1000,
            )

            st.plotly_chart(
                comparison_fig,
                width="stretch",
                key="deposition_comparison",
            )

            if mode == "Simulation Mode":
                st.caption(
                    "Illustrative comparison based on simulated "
                    "charge and manually entered mass values."
                )


    
    st.divider()
    st.subheader("Data Export")

    if st.session_state.running:
        st.info("Pause the simulation to export a stable dataset.")

    elif st.session_state.history:
        csv_data = measurements_to_csv(
            st.session_state.history
        )

        st.download_button(
            label="⬇ Download Measurements (CSV)",
            data=csv_data,
            file_name="ElectroLab_X_simulation.csv",
            mime="text/csv",
            on_click="ignore",
            key="download_measurements",
        )

    else:
        st.info("No measurements have been recorded yet.")


    st.divider()
    st.subheader("Scientific Experiment Report")

    if st.session_state.stopped and st.session_state.history:

        try:
            report_text = generate_experiment_report(
                history=st.session_state.history,
                experiment_name=experiment_name,
                area_cm2=exposed_area_cm2,
                initial_mass_g=initial_mass_g,
                final_mass_g=final_mass_g,
            )

            st.download_button(
                label="⬇ Download Experiment Report",
                data=report_text,
                file_name="ElectroLab_X_Report.txt",
                mime="text/plain",
                on_click="ignore",
                key="download_report",
            )

        except ValueError as exc:
            st.error(f"Report generation failed: {exc}")

    else:
        st.info(
            "Stop the experiment to generate its final report."
        )


live_dashboard()







