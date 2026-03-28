import streamlit as st
import segyio
import numpy as np
import plotly.express as px
import pandas as pd

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
    # Create a synthetic structured dataset
    t = np.linspace(0, 2000, 500)
    data = np.zeros((200, 500))
    for i in range(8):
        depth = np.random.randint(50, 450)
        amp = np.random.uniform(0.5, 1.0)
        data[:, depth:depth+8] += amp * np.sin(2 * np.pi * 0.04 * t[depth:depth+8])
    st.session_state['demo_data'] = data
    st.session_state['data_source'] = "Synthetic Demo"

# Data Loading Logic
data_to_plot = None
if uploaded_file is not None:
    with open("temp_data.segy", "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        with segyio.open("temp_data.segy", "r", ignore_geometry=False) as f:
            data_to_plot = f.iline[f.ilines[len(f.ilines)//2]].T
    except:
        st.error("Format Error.")
elif 'demo_data' in st.session_state:
    data_to_plot = st.session_state['demo_data'].T

# Main Workspace
if data_to_plot is not None:
    st.title("Seismic Interpretation & Analytics")
    
    col_tools, col_main = st.columns([1, 4])
    
    with col_tools:
        st.subheader("Controls")
        horizon_name = st.text_input("Active Horizon", "Target_Reservoir")
        
        if st.button("Reset Session"):
            st.session_state['picks'] = pd.DataFrame(columns=['Trace', 'Time', 'Amplitude', 'Horizon'])
            st.rerun()
            
        st.info("Tip: Use the 'Box Select' or 'Lasso' tool on the right to pick reflectors.")

    with col_main:
        vm = np.percentile(data_to_plot, 98)
        
        # Main Seismic Plot
        fig_seismic = px.imshow(
            data_to_plot,
            color_continuous_scale='RdBu',
            zmin=-vm, zmax=vm,
            labels=dict(x="Trace Index", y="Two-Way Time (ms)", color="Amplitude"),
            aspect='auto'
        )
        fig_seismic.update_layout(template='plotly_dark', height=550, margin=dict(l=10, r=10, t=30, b=10))

        # Event Capture
        event_data = st.plotly_chart(fig_seismic, on_select="rerun", key="seismic_plot", use_container_width=True)
        
        if event_data and "selection" in event_data:
            points = event_data["selection"]["points"]
            if points:
                new_picks = []
                for p in points:
                    # Capture coordinate and the specific amplitude value at that point
                    trace_idx = int(p['x'])
                    time_idx = int(p['y'])
                    # We need to map time_idx to the actual array index safely
                    val = data_to_plot[time_idx, trace_idx]
                    new_picks.append({'Trace': trace_idx, 'Time': time_idx, 'Amplitude': val, 'Horizon': horizon_name})
                
                new_df = pd.DataFrame(new_picks)
                st.session_state['picks'] = pd.concat([st.session_state['picks'], new_df]).drop_duplicates()

    # Analytics Section (Only shows if data is picked)
    if not st.session_state['picks'].empty:
        st.divider()
        st.subheader("Reservoir Attribute Analytics")
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Amplitude vs Depth Cross-Plot
            fig_cross = px.scatter(
                st.session_state['picks'],
                x="Time",
                y="Amplitude",
                color="Horizon",
                title="Amplitude vs. Time (Depth) Distribution",
                template="plotly_dark",
                trendline="ols" # Adds a trendline to see decay or brightening
            )
            st.plotly_chart(fig_cross, use_container_width=True)
            
        with c2:
            st.write("**Pick Statistics**")
            st.dataframe(st.session_state['picks'].describe()[['Amplitude', 'Time']], use_container_width=True)
            
            csv = st.session_state['picks'].to_csv(index=False).encode('utf-8')
            st.download_button("Export Pick Data (CSV)", csv, "seismic_picks.csv", "text/csv", use_container_width=True)

else:
    st.title("SeismicFlow Analytics")
    st.markdown("### Professional Seismic Interpretation Platform")
    st.info("Upload a .segy volume or use the Demo Data button in the sidebar to initialize the workstation.")
