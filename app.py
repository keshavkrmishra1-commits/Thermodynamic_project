import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.colors as pc

st.set_page_config(page_title="Cp vs T Database", layout="wide")

@st.cache_data
def load_data():
    # Updated to read the new file
    df = pd.read_csv("DataFinal.csv")
    
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
        default=[] # Leaves the category filter empty by default
    )
    
    # If a category is picked, filter the list. Otherwise, show all materials.
    if categories:
        filtered_df = df[df['Category'].isin(categories)]
    else:
        filtered_df = df 
else:
    filtered_df = df

# 2. Direct Material Selection
materials = st.sidebar.multiselect(
    "2. Select Materials", 
    options=filtered_df['Material_Name'].unique(), 
    default=filtered_df['Material_Name'].unique()[:2]
)

# 3. User-defined temperature ranges
t_range = st.sidebar.slider("3. Temperature Range (K)", min_value=200, max_value=3000, value=(298, 1500), step=10)

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
    
    # Mask to separate valid temperatures from out-of-bounds temperatures
    valid_mask = (T_vals >= t_min) & (T_vals <= t_max)
    
    # Create two separate arrays: one for the solid line, one for the dashed line
    Cp_valid = np.where(valid_mask, Cp, np.nan)
    Cp_invalid = np.where(~valid_mask, Cp, np.nan)
    
    # Select color so both solid and dashed parts match
    line_color = colors[i % len(colors)]
    
    # Plot Valid Range (Solid Line)
    fig.add_trace(go.Scatter(
        x=T_vals, y=Cp_valid, 
        mode='lines', 
        name=mat, 
        legendgroup=mat,
        line=dict(color=line_color, dash='solid', width=3), 
        hovertemplate="T: %{x:.1f} K<br>Cp: %{y:.2f} J/(mol·K)"
    ))
    
    # Plot Invalid/Extrapolated Range (Dashed Line)
    fig.add_trace(go.Scatter(
        x=T_vals, y=Cp_invalid, 
        mode='lines', 
        name=f"{mat} (Extrapolated)", 
        legendgroup=mat,
        showlegend=False, # Hides from legend so the material only appears once
        line=dict(color=line_color, dash='dash', width=2), 
        hovertemplate="T: %{x:.1f} K<br>Cp: %{y:.2f} J/(mol·K) (Extrapolated)"
    ))

# Clear axis titles, units, and legends
fig.update_layout(
    xaxis_title="Temperature (K)",
    yaxis_title="Specific Heat Capacity, C<sub>p</sub>(J/mol·K)",
    hovermode="x unified",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

st.subheader("Material Properties & Data Sources")
st.dataframe(df[df['Material_Name'].isin(materials)])
