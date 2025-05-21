import streamlit as st
st.write("🔑 Available secret keys:", list(st.secrets.keys()))
st.stop()
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid
import gspread
from google.oauth2.service_account import Credentials

# Streamlit app title
st.title("Live Google Sheet Table with Filters (Authorized)")

# Google Sheets authentication using service account credentials stored in Streamlit secrets
def authorize_gsheets():
    # Credentials JSON stored in secrets.toml under key 'gcp_service_account'
    creds_dict = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client

@st.cache_resource
def get_sheet_dataframe(sheet_id: str, gid: int) -> pd.DataFrame:
    """Fetches a sheet as DataFrame using gspread"""
    client = authorize_gsheets()
    sheet = client.open_by_key(sheet_id).get_worksheet_by_id(gid)
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Configuration
SHEET_ID = "1xqGCXsebSmYL4bqAwvTmD9lOentI45CTMxhea-ZDFls"
GID = 1731969866

# Load data with caching
try:
    df = get_sheet_dataframe(SHEET_ID, GID)
except Exception as e:
    st.error(f"Ошибка авторизации или загрузки данных: {e}")
    st.stop()

# Filter rows where column 'C' == 'active'
if 'C' in df.columns:
    df = df[df['C'] == 'active']
else:
    st.warning("Колонка 'C' не найдена в таблице.")

# Select columns A, B, P, Q, V
cols = [col for col in ['A', 'B', 'P', 'Q', 'V'] if col in df.columns]
df = df[cols]

# Build and display AgGrid with filters
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(filterable=True, sortable=True, resizable=True)
grid_options = gb.build()

AgGrid(
    df,
    gridOptions=grid_options,
    height=400,
    fit_columns_on_grid_load=True
)

st.write("Всего строк:", len(df))

st.markdown("---")
st.markdown(
    "**Инструкция:** Задайте секрет `gcp_service_account` в `.streamlit/secrets.toml` или через Streamlit Cloud UI."
)
