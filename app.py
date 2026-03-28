import streamlit as st
import segyio
import numpy as np
import matplotlib.pyplot as plt
import os

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

# Sidebar Branding
st.sidebar.markdown('<div class="brand-text">SERHOUDJI</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sub-brand">Geological Software Solutions</div>', unsafe_allow_html=True)
st.sidebar.divider()

# Resource Section
st.sidebar.subheader("Data Input")
uploaded_file = st.sidebar.file_uploader("Upload Seismic Volume (.segy / .sgy)", type=["segy", "sgy"])

# Fallback: Synthetic Data Generator
if st.sidebar.button("Generate Demo Seismic Data"):
    # Create a synthetic 3D cube for demonstration
    t = np.linspace(0, 2, 500)
    data = np.zeros((100, 500))
    for i in range(5): # Add some "reflectors"
        depth = np.random.randint(50, 450)
        data[:, depth:depth+5] = np.sin(2 * np.pi * 5 * t[depth:depth+5])
    
    # Simulate a fault/structure
    data = np.roll(data, 20, axis=0) 
    st.session_state['demo_data'] = data
    st.session_state['data_source'] = "Synthetic Demo"
    st.sidebar.success("Demo Data Generated")

# Logic to choose between Uploaded or Demo data
data_to_plot = None
source_name = ""

if uploaded_file is not None:
    with open("temp_data.segy", "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        with segyio.open("temp_data.segy", "r", ignore_geometry=False) as f:
            # Simple logic to grab the middle inline for preview
            data_to_plot = f.iline[f.ilines[len(f.ilines)//2]].T
            source_name = f"SEGY File: {uploaded_file.name}"
    except Exception as e:
        st.error(f"Error reading SEGY: {e}")
elif 'demo_data' in st.session_state:
    data_to_plot = st.session_state['demo_data'].T
    source_name = st.session_state['data_source']

# Main Dashboard
if data_to_plot is not None:
    st.title("Seismic Visualization Dashboard")
    st.caption(f"Active Source: {source_name}")
    
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.subheader("Controls")
        cmap = st.selectbox("Colormap", ["RdBu", "gray", "seismic", "magma"])
        contrast = st.slider("Contrast (%)", 90.0, 100.0, 98.0)
        
    with col2:
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        vm = np.percentile(data_to_plot, contrast)
        im = ax.imshow(data_to_plot, cmap=cmap, vmin=-vm, vmax=vm, aspect='auto')
        
        ax.set_title("Seismic Cross-Section", color='white')
        ax.tick_params(colors='white')
        plt.colorbar(im)
        st.pyplot(fig)
else:
    st.title("SeismicFlow Analytics")
    st.info("Upload a .segy file or click 'Generate Demo Seismic Data' in the sidebar to begin.")
