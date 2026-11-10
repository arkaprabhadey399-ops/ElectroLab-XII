
import pandas as pd
import streamlit as st


from electrolab.calculations import current_density
from electrolab.simulation import ElectroplatingSimulator
from electrolab.experiment import ChargeIntegrator
from electrolab.charts import make_time_series_chart
from electrolab.storage import (
    measurements_to_csv,
    create_experiment_log,
    append_measurement,
)


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

def reset_experiment():
    """Reset simulation and measurement history."""
    st.session_state.simulator = ElectroplatingSimulator()
    st.session_state.integrator = ChargeIntegrator()
    st.session_state.latest_sample = None
    st.session_state.history = []
    st.session_state.running = False
    st.session_state.log_path = None
    st.session_state.log_error = None
    st.session_state.stopped = False


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("⚡ ElectroLab X")

st.caption(
    "Advanced Electrochemical Monitoring & Analysis System"
)

st.divider()


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
        ["Simulation Mode", "Live Arduino Mode"],
    )
    
    exposed_area_cm2 = st.number_input(
        "Exposed Cathode Surface Area (cm²)",
        min_value=0.1,
        value=10.0,
        step=0.5,
        format="%.2f",
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
    if st.button(
        "▶ Start / Resume",
        disabled=(
            mode != "Simulation Mode"
            or st.session_state.running
            or st.session_state.stopped
        ),
    ):
        # Create a CSV file for a new experiment.
        if st.session_state.log_path is None:
            try:
                st.session_state.log_path = create_experiment_log()
            except OSError as exc:
                st.session_state.log_error = str(exc)

        # Start only if the log file exists.
        if st.session_state.log_path is not None:
            st.session_state.log_error = None
            st.session_state.integrator.start()
            st.session_state.running = True

    # PAUSE
    if st.button(
        "⏸ Pause",
        disabled=not st.session_state.running,
    ):
        st.session_state.integrator.pause()
        st.session_state.running = False

    # STOP
    if st.button(
        "⏹ Stop Experiment",
        disabled=(
            st.session_state.stopped
            or not st.session_state.history
        ),
    ):
        st.session_state.integrator.pause()
        st.session_state.running = False
        st.session_state.stopped = True

    # RESET
    if st.button("↺ Reset Experiment"):
        reset_experiment()


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
        st.info("Press Start / Resume to begin simulation.")
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



live_dashboard()





