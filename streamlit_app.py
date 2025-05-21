import streamlit as st
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid

# Title of the app
st.title("Live Google Sheet Table with Filters")

# Google Sheet details
SHEET_ID = "1xqGCXsebSmYL4bqAwvTmD9lOentI45CTMxhea-ZDFls"
GID = "1731969866"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

@st.cache_data(ttl=600)
def load_data():
    """Load data from Google Sheet (cached for 10 minutes)"""
    df = pd.read_csv(CSV_URL)
    return df

# Load and filter data
df = load_data()
# Keep only rows where column 'C' == 'active'
filtered = df[df.get('C', '') == 'active']
# Select only columns A, B, P, Q, V (if they exist)
cols = [col for col in ['A', 'B', 'P', 'Q', 'V'] if col in filtered.columns]
filtered = filtered[cols]

# Build AgGrid options with filters enabled
gb = GridOptionsBuilder.from_dataframe(filtered)
gb.configure_default_column(filterable=True, sortable=True, resizable=True)
grid_options = gb.build()

# Display the interactive grid
AgGrid(
    filtered,
    gridOptions=grid_options,
    enable_enterprise_modules=False,
    height=400,
    fit_columns_on_grid_load=True
)

st.write("Rows: ", len(filtered))

# Instructions
st.markdown("---")
st.markdown(
    "**Usage:** Filter directly in the table headers to refine results by any column."
)

# Run with: streamlit run streamlit_app.py
