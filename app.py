import streamlit as st
import segyio
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="SeismicFlow Analytics", layout="wide")

st.title(" Seismic Data Quick Look")
st.markdown("Extract attributes and visualize subsurface structures instantly.")

uploaded_file = st.file_uploader("Upload a .segy or .sgy file", type=["segy", "sgy"])

if uploaded_file is not None:
    # Save temporary file to read with segyio
    with open("temp.segy", "wb") as f:
        f.write(uploaded_file.getbuffer())

    with segyio.open("temp.segy", "r", ignore_geometry=False) as f:
        # Get Geometry
        inlines = f.ilines
        crosslines = f.xlines
        t_samples = f.samples
        
        st.sidebar.success("File Loaded Successfully!")
        st.sidebar.info(f"Inlines: {inlines.min()} - {inlines.max()}")
        st.sidebar.info(f"Crosslines: {crosslines.min()} - {crosslines.max()}")

        # User Input for Visualization
        view_mode = st.sidebar.radio("Select View", ["Inline", "Crossline"])
        
        if view_mode == "Inline":
            line_idx = st.sidebar.select_slider("Select Inline Number", options=inlines)
            # Extract data
            data = f.iline[line_idx].T
        else:
            line_idx = st.sidebar.select_slider("Select Crossline Number", options=crosslines)
            data = f.xline[line_idx].T

        # Visualization
        fig, ax = plt.subplots(figsize=(10, 6))
        vm = np.percentile(data, 98) # Clipping for better contrast
        im = ax.imshow(data, cmap="RdBu", vmin=-vm, vmax=vm, aspect='auto',
                       extent=[0, data.shape[1], t_samples[-1], t_samples[0]])
        
        ax.set_xlabel("Trace Number")
        ax.set_ylabel("Time (ms)")
        plt.colorbar(im, ax=ax, label="Amplitude")
        st.pyplot(fig)
