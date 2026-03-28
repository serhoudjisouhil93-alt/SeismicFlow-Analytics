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
    .main {
        background-color: #0e1117;
    }
    .stSidebar {
        background-color: #161b22;
    }
    .brand-text {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        color: #58a6ff;
        font-weight: bold;
        font-size: 24px;
        letter-spacing: 1px;
    }
    .sub-brand {
        color: #8b949e;
        font-size: 14px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar Branding
st.sidebar.markdown('<div class="brand-text">SERHOUDJI</div>', unsafe_allow_html=True)
st.sidebar.markdown('<div class="sub-brand">Geological Software Solutions</div>', unsafe_allow_html=True)
st.sidebar.divider()

# Sample Data Section
st.sidebar.subheader("Resources")
st.sidebar.info("To test this application without a local file, download the sample SEGY data below.")

# Button to link to a public seismic sample (e.g., USGS or F3)
st.sidebar.link_button("Download Sample SEGY", "https://github.com/equinor/segyio-notebooks/raw/master/data/small.sgy")

# File Upload Logic
uploaded_file = st.sidebar.file_uploader("Upload Seismic Volume (.segy / .sgy)", type=["segy", "sgy"])

if uploaded_file is not None:
    # Save temporary file
    with open("temp_data.segy", "wb") as f:
        f.write(uploaded_file.getbuffer())

    try:
        with segyio.open("temp_data.segy", "r", ignore_geometry=False) as f:
            # Data Properties
            inlines = f.ilines
            crosslines = f.xlines
            t_samples = f.samples

            # Main Dashboard Header
            st.title("Seismic Attribute Extraction & Visualization")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Inlines", len(inlines))
            col2.metric("Total Crosslines", len(crosslines))
            col3.metric("Time Samples", len(t_samples))

            st.divider()

            # Controls
            c1, c2 = st.columns([1, 3])
            with c1:
                st.subheader("Display Controls")
                mode = st.radio("Orientation", ["Inline", "Crossline"])
                colormap = st.selectbox("Colormap", ["RdBu", "gray", "seismic", "PuOr"])
                
                if mode == "Inline":
                    idx = st.select_slider("Select Line", options=inlines)
                    data = f.iline[idx].T
                else:
                    idx = st.select_slider("Select Line", options=crosslines)
                    data = f.xline[idx].T

            # Plotting
            with c2:
                fig, ax = plt.subplots(figsize=(12, 7))
                fig.patch.set_facecolor('#0e1117')
                ax.set_facecolor('#0e1117')
                
                # Normalize for visibility
                vm = np.percentile(data, 99)
                
                im = ax.imshow(data, cmap=colormap, vmin=-vm, vmax=vm, aspect='auto',
                               extent=[0, data.shape[1], t_samples[-1], t_samples[0]])
                
                ax.set_title(f"Seismic Section: {mode} {idx}", color='white', fontsize=14)
                ax.set_xlabel("Trace Index", color='white')
                ax.set_ylabel("Two-Way Time (ms)", color='white')
                ax.tick_params(colors='white')
                
                cbar = plt.colorbar(im)
                cbar.ax.yaxis.set_tick_params(color='white')
                plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='white')
                
                st.pyplot(fig)

    except Exception as e:
        st.error(f"Error processing SEGY file: {e}")
else:
    st.title("SeismicFlow Analytics")
    st.info("Please upload a SEGY file from the sidebar or download the sample to begin analysis.")
    st.markdown("""
    ### Current Capabilities
    * **Dynamic Visualization:** Interactive slicing of 3D seismic volumes.
    * **Geometry Extraction:** Automatic detection of inline and crossline ranges.
    * **Adaptive Normalization:** High-contrast visualization using percentile clipping.
    """)
