import streamlit as st
import segyio
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from scipy.fft import fft, fftfreq
import google.generativeai as genai

# --- PROFESSIONAL CONFIGURATION ---
st.set_page_config(
    page_title="SeismicFlow Analytics | Serhoudji",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Professional Theme (GitHub Dark Style)
st.markdown("""
    <style>
    .main { background-color: #0d1117; }
    .stSidebar { background-color: #161b22; border-right: 1px solid #30363d; }
    .brand-text {
        font-family: 'Inter', sans-serif;
        color: #58a6ff;
        font-weight: 800;
        font-size: 26px;
        letter-spacing: -1px;
    }
    .sub-brand { color: #8b949e; font-size: 13px; margin-bottom: 25px; text-transform: uppercase; }
    div[data-testid="stMetricValue"] { color: #58a6ff; font-size: 24px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #21262d; color: #c9d1d9; border: 1px solid #30363d; }
    .stButton>button:hover { border-color: #58a6ff; color: #58a6ff; }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'picks' not in st.session_state:
    st.session_state['picks'] = pd.DataFrame(columns=['Trace', 'Time', 'Amplitude', 'Horizon'])

# --- SIDEBAR BRANDING & INPUT ---
with st.sidebar:
    st.markdown('<div class="brand-text">SERHOUDJI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-brand">Subsurface Intelligence Lab</div>', unsafe_allow_html=True)
    
    st.subheader("Data Management")
    uploaded_file = st.file_uploader("Upload SEGY/SGY Volume", type=["segy", "sgy"])
    
    if st.button("Generate Synthetic Demo Data"):
        t = np.linspace(0, 2000, 500)
        data = np.zeros((200, 500))
        for i in range(10):
            depth = np.random.randint(50, 450)
            amp = np.random.uniform(0.4, 1.0)
            freq = np.random.uniform(25, 50)
            data[:, depth:depth+6] += amp * np.sin(2 * np.pi * freq * (t[depth:depth+6]/1000))
        st.session_state['demo_data'] = data
        st.session_state['data_source'] = "Synthetic Field Demo"

    st.divider()
    st.subheader("AI Copilot Settings")
    api_key = st.text_input("Gemini API Key", type="password", help="Get a free key at aistudio.google.com")

# --- DATA PROCESSING LOGIC ---
data_to_plot = None
dt = 0.004 # Default 4ms

if uploaded_file is not None:
    with open("temp.segy", "wb") as f:
        f.write(uploaded_file.getbuffer())
    try:
        with segyio.open("temp.segy", "r", ignore_geometry=False) as f:
            data_to_plot = f.iline[f.ilines[len(f.ilines)//2]].T
            dt = segyio.tools.dt(f) / 1e6
    except Exception as e:
        st.error(f"SEGY Read Error: {e}")
elif 'demo_data' in st.session_state:
    data_to_plot = st.session_state['demo_data'].T

# --- MAIN INTERFACE ---
if data_to_plot is not None:
    st.title("SeismicFlow: Advanced Workstation")
    
    # KPI Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Vertical Resolution", f"{int(1/(4*dt*30))}m", delta="Estimated")
    m2.metric("Sample Interval", f"{dt*1000} ms")
    m3.metric("Picked Points", len(st.session_state['picks']))

    # Layout: Visualizer + Interpretation Tools
    col_tools, col_main = st.columns([1, 4])

    with col_tools:
        st.subheader("Interpretation")
        h_name = st.text_input("Horizon Name", "Target_Unit_1")
        if st.button("Clear Interpretation"):
            st.session_state['picks'] = pd.DataFrame(columns=['Trace', 'Time', 'Amplitude', 'Horizon'])
            st.rerun()
        
        st.info("Use Box/Lasso Select tools on the seismic plot to interpret horizons.")

    with col_main:
        vm = np.percentile(data_to_plot, 98)
        fig = px.imshow(
            data_to_plot, color_continuous_scale='RdBu',
            zmin=-vm, zmax=vm, aspect='auto',
            labels=dict(x="Trace Index", y="TWT (ms)", color="Amp")
        )
        fig.update_layout(template='plotly_dark', height=550, margin=dict(l=0,r=0,t=0,b=0))
        
        select_data = st.plotly_chart(fig, on_select="rerun", key="main_plot", use_container_width=True)

        # Logic for selection
        if select_data and "selection" in select_data:
            pts = select_data["selection"]["points"]
            if pts:
                new_pts = []
                for p in pts:
                    tr, ti = int(p['x']), int(p['y'])
                    new_pts.append({'Trace': tr, 'Time': ti, 'Amplitude': data_to_plot[ti, tr], 'Horizon': h_name})
                st.session_state['picks'] = pd.concat([st.session_state['picks'], pd.DataFrame(new_pts)]).drop_duplicates()

    # --- ADVANCED ANALYTICS SECTION ---
    if not st.session_state['picks'].empty:
        st.divider()
        st.subheader("Subsurface Analytics & AI Reporting")
        
        ana1, ana2 = st.columns(2)
        
        with ana1:
            # Amplitude vs Depth
            fig_scat = px.scatter(st.session_state['picks'], x="Time", y="Amplitude", color="Horizon", 
                                 title="Amplitude Decay vs Depth", template="plotly_dark", trendline="ols")
            st.plotly_chart(fig_scat, use_container_width=True)
        
        with ana2:
            # Frequency Spectrum of the last picked trace
            last_trace_idx = int(st.session_state['picks'].iloc[-1]['Trace'])
            trace_data = data_to_plot[:, last_trace_idx]
            N = len(trace_data)
            yf = fft(trace_data)
            xf = fftfreq(N, dt)[:N//2]
            psd = 2.0/N * np.abs(yf[0:N//2])
            
            fig_freq = go.Figure(data=go.Scatter(x=xf, y=psd, line=dict(color='#58a6ff')))
            fig_freq.update_layout(title=f"Frequency Spectrum (Trace {last_trace_idx})", 
                                  template="plotly_dark", xaxis_range=[0, 70], xaxis_title="Hz")
            st.plotly_chart(fig_freq, use_container_width=True)

        # --- AI COPILOT REPORT GENERATION ---
        st.divider()
        if api_key:
            if st.button("🚀 Generate AI Geological Report"):
                try:
                    genai.configure(api_key=api_key)
                    ai_model = genai.GenerativeModel('gemini-1.5-flash')
                    
                    # Data context for AI
                    avg_amp = st.session_state['picks']['Amplitude'].mean()
                    peak_freq = xf[np.argmax(psd)]
                    
                    prompt = f"""
                    Context: SBAA Basin (Upper Devonian source rock logic).
                    Analyze this seismic data:
                    - Horizon: {h_name}
                    - Mean Amplitude: {avg_amp:.4f}
                    - Peak Frequency: {peak_freq:.1f} Hz
                    Write a professional technical summary. Evaluate the hydrocarbon potential if high amplitudes are present.
                    """
                    
                    with st.spinner("Serhoudji AI is analyzing..."):
                        response = ai_model.generate_content(prompt)
                        st.markdown("### AI Copilot Interpretation")
                        st.write(response.text)
                except Exception as e:
                    st.error(f"AI Error: {e}")
        else:
            st.warning("Enter Gemini API Key in the sidebar to enable the AI Copilot.")

else:
    st.title("SeismicFlow Analytics")
    st.info("Awaiting Data Input. Upload a SEGY volume or generate a demo model from the sidebar.")
    st.markdown("""
    **Core Capabilities:**
    * 3D Seismic Volume Navigation (Inline/Crossline)
    * Real-time Horizon Picking & Interpretation
    * Spectral Frequency Analysis (FFT)
    * Agentic AI Reporting & Reservoir Characterization
    """)
