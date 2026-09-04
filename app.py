import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pc

st.set_page_config(page_title="Cp vs T Database", layout="wide")

@st.cache_data
def load_data():
    # Read the data file
    df = pd.read_csv("DataFinal.csv")
    
    # Merge duplicate categories by standardizing capitalization
    if 'Category' in df.columns:
        df['Category'] = df['Category'].replace({'semiconductors': 'Semiconductors'})
    
    # Force thermodynamic coefficient columns to be numeric
    cols_to_convert = ['A', 'B', 'C', 'D', 'E']
    for col in cols_to_convert:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
    # Clean trailing empty columns from CSV export
    return df.loc[:, ~df.columns.str.contains('^Unnamed')]

df = load_data()

st.title("Interactive Thermodynamic Database: $C_p$ vs T")

st.sidebar.header("Interactive Controls")

# 1. Optional Category Filter
if 'Category' in df.columns:
    categories = st.sidebar.multiselect(
        "1. Filter by Category (Optional)", 
        options=df['Category'].unique(), 
        default=[]
    )
    if categories:
        filtered_df = df[df['Category'].isin(categories)]
    else:
        filtered_df = df 
else:
    filtered_df = df

# 2. Direct Material Selection
materials = st.sidebar.multiselect(
    "2. Select Materials for Graph", 
    options=filtered_df['Material_Name'].unique(), 
    default=filtered_df['Material_Name'].unique()[:2]
)

# 3. User-defined temperature ranges
t_range = st.sidebar.slider("3. Graph Temperature Range (K)", min_value=200, max_value=3000, value=(298, 1500), step=10)

# --- GRAPH GENERATION ---
fig = go.Figure()
T_vals = np.linspace(t_range[0], t_range[1], 500)
colors = pc.qualitative.Plotly

for i, mat in enumerate(materials):
    mat_data = df[df['Material_Name'] == mat].iloc[0]
    t_min = mat_data['T_min_K']
    t_max = mat_data['T_max_K']
    
    t = T_vals / 1000.0
    
    # Shomate Equation implementation
    Cp = mat_data['A'] + mat_data['B']*t + mat_data['C']*(t**2) + mat_data['D']*(t**3) + mat_data['E']/(t**2)
    
    valid_mask = (T_vals >= t_min) & (T_vals <= t_max)
    Cp_valid = np.where(valid_mask, Cp, np.nan)
    Cp_invalid = np.where(~valid_mask, Cp, np.nan)
    
    line_color = colors[i % len(colors)]
    
    # Solid Line (Valid Range)
    fig.add_trace(go.Scatter(
        x=T_vals, y=Cp_valid, 
        mode='lines', name=mat, legendgroup=mat,
        line=dict(color=line_color, dash='solid', width=3), 
        hovertemplate="T: %{x:.1f} K<br>Cp: %{y:.2f} J/(mol·K)"
    ))
    
    # Dashed Line (Extrapolated Range)
    fig.add_trace(go.Scatter(
        x=T_vals, y=Cp_invalid, 
        mode='lines', name=f"{mat} (Extrapolated)", legendgroup=mat, showlegend=False,
        line=dict(color=line_color, dash='dash', width=2), 
        hovertemplate="T: %{x:.1f} K<br>Cp: %{y:.2f} J/(mol·K) (Extrapolated)"
    ))

fig.update_layout(
    xaxis_title="Temperature (K)",
    yaxis_title="Specific Heat Capacity, C<sub>p</sub> (J/mol·K)",
    hovermode="x unified",
    template="plotly_white"
)
st.plotly_chart(fig, use_container_width=True)

# --- NEW: EXACT VALUE CALCULATOR ---
st.subheader("Calculate Exact $C_p$ Value")
st.write("Find the precise specific heat capacity of a material at a specific temperature.")

col1, col2 = st.columns(2)
with col1:
    calc_mat = st.selectbox("Select a Material", options=df['Material_Name'].unique())
with col2:
    calc_temp = st.number_input("Enter Temperature (K)", min_value=1.0, max_value=6000.0, value=298.15, step=1.0)

if calc_mat:
    mat_data_calc = df[df['Material_Name'] == calc_mat].iloc[0]
    t_calc = calc_temp / 1000.0
    
    # Calculate exact point using Shomate equation
    cp_calc = mat_data_calc['A'] + mat_data_calc['B']*t_calc + mat_data_calc['C']*(t_calc**2) + mat_data_calc['D']*(t_calc**3) + mat_data_calc['E']/(t_calc**2)
    
    t_min_calc = mat_data_calc['T_min_K']
    t_max_calc = mat_data_calc['T_max_K']
    
    # Display the result in a clean box
    st.info(f"**Specific Heat Capacity for {calc_mat} at {calc_temp} K:** {cp_calc:.4f} J/(mol·K)")
    
    # Warn if the exact point is extrapolated
    if calc_temp < t_min_calc or calc_temp > t_max_calc:
        st.warning(f"⚠️ **Note:** {calc_temp} K is outside the valid temperature range ({t_min_calc} K – {t_max_calc} K) for {calc_mat}. This is an extrapolated value.")

st.divider()

# --- MATERIAL DATABASE ---
st.subheader("Material Properties & Data Sources")
st.dataframe(df[df['Material_Name'].isin(materials)])
