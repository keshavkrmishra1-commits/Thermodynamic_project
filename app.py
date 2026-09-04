import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pc

# Page configuration
st.set_page_config(page_title="Cp Data Platform", page_icon="🔥", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_csv("DataFinal.csv")
    if 'Category' in df.columns:
        df['Category'] = df['Category'].replace({'semiconductors': 'Semiconductors'})
    cols_to_convert = ['A', 'B', 'C', 'D', 'E']
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

df = load_data()

# Custom Dashboard Header
st.markdown("<h1 style='text-align: center; color: #5DADE2;'>Thermodynamic Property Database</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; font-size: 1.1em; color: #7F8C8D;'>MCR-202 Project Submission • Department of Ceramic Engineering</p>", unsafe_allow_html=True)
st.divider()

# Sidebar Configuration
st.sidebar.markdown("### 🎛️ Control Panel")
st.sidebar.caption("Adjust parameters to dynamically update the visualization.")

if 'Category' in df.columns:
    categories = st.sidebar.multiselect("Filter by Category (Optional)", options=df['Category'].unique(), default=[])
    filtered_df = df[df['Category'].isin(categories)] if categories else df
else:
    filtered_df = df

materials = st.sidebar.multiselect("Select Materials to Plot", options=filtered_df['Material_Name'].unique(), default=filtered_df['Material_Name'].unique()[:2])
t_range = st.sidebar.slider("Temperature Range (K)", min_value=200.0, max_value=3000.0, value=(298.0, 1500.0), step=1.0)
show_extrap = st.sidebar.checkbox("Show Extrapolated Ranges", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("**About This Tool**")
st.sidebar.caption("Computes specific heat capacity ($C_p$) via the Shomate Equation. Solid lines indicate experimentally valid boundaries. Dashed lines represent theoretical extrapolation.")

# --- GRAPH GENERATION ---
fig = go.Figure()
T_vals = np.linspace(t_range[0], t_range[1], 3000)
colors = pc.qualitative.Safe  # Switched to a more professional color palette

for i, mat in enumerate(materials):
    mat_data = df[df['Material_Name'] == mat].iloc[0]
    t_min = mat_data['T_min_K']
    t_max = mat_data['T_max_K']
    
    T_mat = np.unique(np.sort(np.append(T_vals, [t_min, t_max])))
    T_mat = T_mat[(T_mat >= t_range[0]) & (T_mat <= t_range[1])]
    t = T_mat / 1000.0
    
    Cp = mat_data['A'] + mat_data['B']*t + mat_data['C']*(t**2) + mat_data['D']*(t**3) + mat_data['E']/(t**2)
    
    valid_mask = (T_mat >= t_min) & (T_mat <= t_max)
    Cp_valid = np.where(valid_mask, Cp, np.nan)
    Cp_invalid = np.where(~valid_mask, Cp, np.nan)
    line_color = colors[i % len(colors)]
    
    fig.add_trace(go.Scatter(x=T_mat, y=Cp_valid, mode='lines', name=mat, legendgroup=mat, line=dict(color=line_color, dash='solid', width=3), hovertemplate="T: %{x:.1f} K<br>Cp: %{y:.2f} J/(mol·K)"))
    
    if show_extrap:
        fig.add_trace(go.Scatter(x=T_mat, y=Cp_invalid, mode='lines', name=f"{mat} (Extrapolated)", legendgroup=mat, showlegend=False, line=dict(color=line_color, dash='dash', width=1.5), hovertemplate="T: %{x:.1f} K<br>Cp: %{y:.2f} J/(mol·K) (Extrapolated)"))

fig.update_layout(xaxis_title="Temperature (K)", yaxis_title="Specific Heat Capacity, C<sub>p</sub> (J/mol·K)", hovermode="x unified", template="plotly_white", margin=dict(l=20, r=20, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
st.plotly_chart(fig, use_container_width=True)

# --- EXACT VALUE CALCULATOR ---
st.markdown("### 📌 Single-Point Analysis")
col1, col2, col3 = st.columns([1, 1, 2])

with col1:
    calc_mat = st.selectbox("Target Material", options=df['Material_Name'].unique())
with col2:
    calc_temp = st.number_input("Target Temperature (K)", min_value=1.0, max_value=6000.0, value=298.15, step=1.0)

with col3:
    if calc_mat:
        mat_data_calc = df[df['Material_Name'] == calc_mat].iloc[0]
        t_calc = calc_temp / 1000.0
        cp_calc = mat_data_calc['A'] + mat_data_calc['B']*t_calc + mat_data_calc['C']*(t_calc**2) + mat_data_calc['D']*(t_calc**3) + mat_data_calc['E']/(t_calc**2)
        t_min_calc, t_max_calc = mat_data_calc['T_min_K'], mat_data_calc['T_max_K']
        
        # Using Streamlit's native Metric widget for a professional dashboard look
        st.metric(label=f"Computed C_p for {calc_mat} at {calc_temp} K", value=f"{cp_calc:.3f} J/(mol·K)")
        
        if calc_temp < t_min_calc or calc_temp > t_max_calc:
            st.caption(f"⚠️ **Note:** Value is extrapolated. Valid domain for {calc_mat} is {t_min_calc} K to {t_max_calc} K.")

# --- EXPANDER FOR RAW DATA ---
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📚 View Raw Thermodynamic Coefficients"):
    st.dataframe(df[df['Material_Name'].isin(materials)], use_container_width=True)
