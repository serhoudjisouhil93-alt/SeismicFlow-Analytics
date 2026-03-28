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
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State for Horizon Picking
if 'picks' not in st.session_state:
    st.session_state['picks'] = pd.DataFrame(columns=['Trace', 'Time', 'Horizon'])

# Sidebar Branding
st.sidebar.markdown('<div class="brand-text">SERHOUDJI</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sub-brand">Geological Software Solutions</div>', unsafe_allow_html=True)
st.sidebar.divider()

# Resource Section
st.sidebar.subheader("Data Input")
uploaded_file = st.sidebar.file_uploader("Upload Seismic Volume (.segy / .sgy)", type=["segy", "sgy"])

# Fallback: Synthetic Data Generator
if st.sidebar.button("Generate Demo Seismic Data"):
    t = np.linspace(0, 2000, 500)
    data = np.random.normal(0, 0.1, (100, 500))
    for i in range(5):
        depth = np.random.randint(50, 450)
        data[:, depth:depth+10] += np.sin(2 * np.pi * 0.05 * t[depth:depth+10])
    st.session_state['demo_data'] = data
    st.session_state['data_source'] = "Synthetic Demo"

# Logic to choose data
data_to_plot = None
if uploaded_file is not None:
    with open("temp_data.segy", "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        with segyio.open("temp_data.segy", "r", ignore_geometry=False) as f:
            data_to_plot = f.iline[f.ilines[len(f.ilines)//2]].T
    except:
        st.error("Error reading file.")
elif 'demo_data' in st.session_state:
    data_to_plot = st.session_state['demo_data'].T

# Main Dashboard
if data_to_plot is not None:
    st.title("Seismic Interpretation Workstation")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.subheader("Interpretation Tools")
        horizon_name = st.text_input("Horizon Name", "Horizon_A")
        if st.button("Clear All Picks"):
            st.session_state['picks'] = pd.DataFrame(columns=['Trace', 'Time', 'Horizon'])
            st.rerun()
        
        st.divider()
        st.write("**Instructions:**")
        st.write("1. Use the Box Select tool on the chart.")
        st.write("2. Selected points will be saved to your horizon table.")
        
    with col2:
        # Normalize Data
        vm = np.percentile(data_to_plot, 98)
        
        # Create Plotly Heatmap
        fig = px.imshow(
            data_to_plot,
            color_continuous_scale='RdBu',
            zmin=-vm, zmax=vm,
            labels=dict(x="Trace Index", y="Time (ms)", color="Amplitude"),
            aspect='auto'
        )
        
        fig.update_layout(
            template='plotly_dark',
            margin=dict(l=20, r=20, t=40, b=20),
            height=600
        )

        # Handle Selection Events
        selected_points = st.plotly_chart(fig, on_select="rerun", key="seismic_plot")
        
        if selected_points and "selection" in selected_points:
            new_points = selected_points["selection"]["points"]
            if new_points:
                temp_df = pd.DataFrame([
                    {'Trace': p['x'], 'Time': p['y'], 'Horizon': horizon_name} 
                    for p in new_points
                ])
                st.session_state['picks'] = pd.concat([st.session_state['picks'], temp_df]).drop_duplicates()

    # Display Horizon Table
    if not st.session_state['picks'].empty:
        st.divider()
        st.subheader("Export Interpretation")
        st.dataframe(st.session_state['picks'], use_container_width=True)
        csv = st.session_state['picks'].to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Horizon", csv, "interpreted_horizon.csv", "text/csv")

else:
    st.title("SeismicFlow Analytics")
    st.info("Upload a .segy file or generate demo data to begin picking horizons.")
