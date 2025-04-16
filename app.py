import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(layout="wide", page_title="Token Emissions Calculator")

st.title("Token Emissions Calculator")

# Sidebar for inputs
with st.sidebar:
    st.header("Model Parameters")
    
    cap = st.number_input("Hard Cap (tokens)", min_value=1.0, value=2.5e9, format="%.1e")
    start_tvl = st.number_input("Initial TVL", min_value=1.0, value=50e6, format="%.1e")
    delta_max = st.number_input("Max Tokens Per Day", min_value=1.0, value=100e6, format="%.1e")
    alpha = st.number_input("Alpha Parameter", min_value=1e-10, value=1e-5, format="%.1e")
    
    st.header("Simulation Length")
    years = st.slider("Years to Simulate", min_value=1, max_value=20, value=10)
    
    st.header("TVL Trajectory Parameters")
    
    # Linear growth parameters
    st.subheader("Linear Growth")
    growth_rate = st.slider("Growth Rate (Linear)", min_value=0.001, max_value=0.05, value=0.01, step=0.001, format="%.3f")
    
    # Sinusoidal parameters
    st.subheader("Sinusoidal Growth")
    sin_growth_rate = st.slider("Growth Rate (Sinusoidal)", min_value=0.001, max_value=0.05, value=0.005, step=0.001, format="%.3f")
    amplitude = st.number_input("Amplitude", min_value=1.0, value=2e7, format="%.1e")
    period = st.slider("Period (days)", min_value=30, max_value=730, value=365)
    
    # Exponential growth parameters
    st.subheader("Exponential Growth")
    exp_growth_rate = st.slider("Growth Rate (Exponential)", min_value=0.0001, max_value=0.01, value=0.001, step=0.0001, format="%.4f")
    
    # S-curve parameters
    st.subheader("S-Curve Growth")
    s_curve_midpoint = st.slider("Midpoint (days)", min_value=100, max_value=3650, value=1825)
    s_curve_steepness = st.slider("Steepness", min_value=0.001, max_value=0.05, value=0.005, step=0.001)
    s_curve_max_tvl = st.number_input("Max TVL", min_value=start_tvl, value=5e9, format="%.1e")

# Create epochs (days)
days = 365 * years
epochs = np.linspace(0, days-1, days)  # One point per day

# TVL trajectory functions
def increasing_tvl(t, start=start_tvl, growth_rate=growth_rate):
    return start * (1 + growth_rate * t)

def sinusoidal_increasing_tvl(t, start=start_tvl, growth_rate=sin_growth_rate, amplitude=amplitude, period=period):
    trend = start * (1 + growth_rate * t)
    seasonal = amplitude * np.sin(2 * np.pi * t / period)
    return trend + seasonal

def exponential_tvl(t, start=start_tvl, growth_rate=exp_growth_rate):
    return start * np.exp(growth_rate * t)

def s_curve_tvl(t, start=start_tvl, max_tvl=s_curve_max_tvl, midpoint=s_curve_midpoint, steepness=s_curve_steepness):
    return start + (max_tvl - start) / (1 + np.exp(-steepness * (t - midpoint)))

# Calculate emissions for a given TVL trajectory
def calculate_emissions(tvl_trajectory):
    tvl_values = tvl_trajectory(epochs)
    minted_so_far = np.zeros_like(epochs)
    emissions = np.zeros_like(epochs)
    
    for t in range(len(epochs)):
        # Cap remaining factor
        g_cap = 1 - minted_so_far[t] / cap
        
        # Inverse TVL factor
        f_tvl = 1 / (1 + alpha * tvl_values[t])
        
        # Provisional emission
        e_t = delta_max * g_cap * f_tvl
        
        # Hard cap enforcement
        e_actual = min(e_t, cap - minted_so_far[t])
        emissions[t] = e_actual
        
        # Update minted so far for next epoch
        if t < len(epochs) - 1:
            minted_so_far[t + 1] = minted_so_far[t] + e_actual
    
    return tvl_values, emissions, minted_so_far

# List of TVL trajectories with their labels
trajectories = [
    (increasing_tvl, "Linear Growth"),
    (sinusoidal_increasing_tvl, "Sinusoidal Growth"),
    (exponential_tvl, "Exponential Growth"),
    (s_curve_tvl, "S-Curve Growth")
]

# Create plotly figure
fig = make_subplots(rows=1, cols=3, 
                   subplot_titles=("TVL Trajectory", "Daily Emissions", "Cumulative Distributed"),
                   shared_yaxes=False,
                   horizontal_spacing=0.05)

# Colors for different trajectories
colors = ['blue', 'red', 'green', 'purple']

# Calculate and plot each trajectory
for idx, (tvl_func, label) in enumerate(trajectories):
    tvl_values, emissions, minted_so_far = calculate_emissions(tvl_func)
    
    # Plot TVL trajectory
    fig.add_trace(
        go.Scatter(x=epochs/365, y=tvl_values/1e6, name="", 
                   line=dict(color=colors[idx])),
        row=1, col=1
    )
    
    # Plot daily emissions
    fig.add_trace(
        go.Scatter(x=epochs/365, y=emissions, name="", 
                   line=dict(color=colors[idx])),
        row=1, col=2
    )
    
    # Plot cumulative emissions
    fig.add_trace(
        go.Scatter(x=epochs/365, y=minted_so_far/1e6, name="", 
                   line=dict(color=colors[idx])),
        row=1, col=3
    )

# Add cap line to cumulative plot
fig.add_trace(
    go.Scatter(x=[0, years], y=[cap/1e6, cap/1e6], name="", 
               line=dict(color='black', width=2, dash='dash')),
    row=1, col=3
)

# Update layout
fig.update_layout(
    height=500,
    width=1100,
    yaxis_title="TVL (millions)",
    yaxis2_title="Tokens per Day",
    yaxis3_title="Tokens (millions)",
)

fig.update_xaxes(title_text="Years", row=1, col=1)
fig.update_xaxes(title_text="Years", row=1, col=2)
fig.update_xaxes(title_text="Years", row=1, col=3)

st.plotly_chart(fig, use_container_width=True)

# Add a legend below the charts
st.markdown("""
<style>
.legend-item {
    display: inline-block;
    margin-right: 20px;
}
.color-box {
    display: inline-block;
    width: 15px;
    height: 15px;
    margin-right: 5px;
    vertical-align: middle;
}
</style>
<div>
    <div class="legend-item"><span class="color-box" style="background-color:blue;"></span>Linear Growth</div>
    <div class="legend-item"><span class="color-box" style="background-color:red;"></span>Sinusoidal Growth</div>
    <div class="legend-item"><span class="color-box" style="background-color:green;"></span>Exponential Growth</div>
    <div class="legend-item"><span class="color-box" style="background-color:purple;"></span>S-Curve Growth</div>
</div>
""", unsafe_allow_html=True)

# Display current parameters
st.subheader("Current Parameters")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Hard Cap", f"{cap/1e9:.2f}B tokens")
    st.metric("Initial TVL", f"{start_tvl/1e6:.2f}M")
with col2:
    st.metric("Max Daily Tokens", f"{delta_max/1e6:.2f}M")
    # st.metric("Initial Emission", f"{e0}")
with col3:
    st.metric("Alpha", f"{alpha:.1e}")
    st.metric("Years Simulated", f"{years}")