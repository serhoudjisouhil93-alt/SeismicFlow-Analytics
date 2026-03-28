import streamlit as st
import segyio
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from scipy.fft import fft, fftfreq

# Professional Page Configuration
st.set_page_config(
    page_title="SeismicFlow Analytics | Serhoudji",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Branding
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stSidebar { background-color: #161b22; }
    .brand-text {
        font-family: 'Segoe UI', sans-serif;
        color: #58a6ff;
        font-weight: bold;
        font-size: 24px;
        letter-spacing: 1px;
    }
    .sub-brand { color: #8b949e; font-size: 14px; margin-bottom: 20px; }
    .stMetric { background-color: #1c2128; padding: 15px; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if 'picks' not in st.session_state:
    st.session_state['picks'] = pd.DataFrame(columns=['Trace', 'Time', 'Amplitude', 'Horizon'])

# Sidebar Branding
st.sidebar.markdown('<div class="brand-text">SERHOUDJI</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sub-brand">Geological Software Solutions</div>', unsafe_allow_html=True)
st.sidebar.divider()

# Resource Section
st.sidebar.subheader("Data Input")
uploaded_file = st.sidebar.file_uploader("Upload Seismic Volume (.segy / .sgy)", type=["segy", "sgy"])

if st.sidebar.button("Generate Demo Seismic Data"):
    t = np.linspace(0, 2000, 500)
    data = np.zeros((200, 500))
    for i in range(8):
        depth = np.random.randint(50, 450)
        amp = np.random.uniform(0.5, 1.0)
        # Mix of different frequencies for the demo
        freq = np.random.uniform(20, 45) 
        data[:, depth:depth+8] += amp * np.sin(2 * np.pi * freq * (t[depth:depth+8]/1000))
    st.session_state['demo_data'] = data
    st.session_state['data_source'] = "Synthetic Demo"

# Data Loading Logic
data_to_plot = None
dt = 0.004 # Default 4ms sampling interval
if uploaded_file is not None:
    with open("temp_data.segy", "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        with segyio.open("temp_data.segy", "r", ignore_geometry=False) as f:
            data_to_plot = f.iline[f.ilines[len(f.ilines)//2]].T
            dt = segyio.tools.dt(f) / 1e6 # Convert microseconds to seconds
    except:
        st.error("Format Error.")
elif 'demo_data' in st.session_state:
    data_to_plot = st.session_state['demo_data'].T

# Main Workspace
if data_to_plot is not None:
    st.title("Seismic Interpretation & Advanced Analytics")
    
    col_tools, col_main = st.columns([1, 4])
    
    with col_tools:
        st.subheader("Controls")
        horizon_name = st.text_input("Active Horizon", "Target_Reservoir")
        if st.button("Reset Session"):
            st.session_state['picks'] = pd.DataFrame(columns=['Trace', 'Time', 'Amplitude', 'Horizon'])
            st.rerun()
        st.info("Select data points to view the Frequency Spectrum.")

    with col_main:
        vm = np.percentile(data_to_plot, 98)
        fig_seismic = px.imshow(
            data_to_plot,
            color_continuous_scale='RdBu',
            zmin=-vm, zmax=vm,
            labels=dict(x="Trace Index", y="Time (ms)", color="Amplitude"),
            aspect='auto'
        )
        fig_seismic.update_layout(template='plotly_dark', height=500, margin=dict(l=10, r=10, t=30, b=10))
        event_data = st.plotly_chart(fig_seismic, on_select="rerun", key="seismic_plot", use_container_width=True)
        
        if event_data and "selection" in event_data:
            points = event_data["selection"]["points"]
            if points:
                new_picks = []
                for p in points:
                    trace_idx, time_idx = int(p['x']), int(p['y'])
                    val = data_to_plot[time_idx, trace_idx]
                    new_picks.append({'Trace': trace_idx, 'Time': time_idx, 'Amplitude': val, 'Horizon': horizon_name})
                st.session_state['picks'] = pd.concat([st.session_state['picks'], pd.DataFrame(new_picks)]).drop_duplicates()

    # Analytics Section
    if not st.session_state['picks'].empty:
        st.divider()
        st.subheader("Frequency & Attribute Analytics")
        
        c1, c2 = st.columns(2)
        
        with c1:
            # Cross-Plot
            fig_cross = px.scatter(st.session_state['picks'], x="Time", y="Amplitude", color="Horizon",
                                 title="Amplitude vs. Time Distribution", template="plotly_dark", trendline="ols")
            st.plotly_chart(fig_cross, use_container_width=True)
            
        with c2:
            # Frequency Spectrum Logic
            # Take the first selected trace as a representative sample for the spectrum
            sample_trace_idx = int(st.session_state['picks'].iloc[-1]['Trace'])
            trace_data = data_to_plot[:, sample_trace_idx]
            
            N = len(trace_data)
            yf = fft(trace_data)
            xf = fftfreq(N, dt)[:N//2]
            psd = 2.0/N * np.abs(yf[0:N//2])
            
            fig_spec = go.Figure()
            fig_spec.add_trace(go.Scatter(x=xf, y=psd, mode='lines', line=dict(color='#58a6ff', width=2)))
            fig_spec.update_layout(
                title=f"Power Spectrum (Trace {sample_trace_idx})",
                xaxis_title="Frequency (Hz)", yaxis_title="Relative Amplitude",
                template="plotly_dark", xaxis_range=[0, 80] # Typical seismic bandwidth
            )
            st.plotly_chart(fig_spec, use_container_width=True)

else:
    st.title("SeismicFlow Analytics")
    st.info("Upload a .segy volume or use the Demo Data button to initialize.")
