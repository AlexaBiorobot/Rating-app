import streamlit as st
import json
import time
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid
import gspread
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

st.set_page_config(page_title="Live Google Sheet Table", layout="wide")
st.title("Live Google Sheet Table with Filters (Authorized)")

def authorize_gsheets():
    if "GCP_SERVICE_ACCOUNT" not in st.secrets:
        st.error("Секрет GCP_SERVICE_ACCOUNT не найден. Проверьте Settings → Secrets.")
        st.stop()

    try:
        sa_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    except json.JSONDecodeError as e:
        st.error(f"Невалидный JSON в GCP_SERVICE_ACCOUNT: {e}")
        st.stop()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_sheet_with_retry(sheet_id: str, gid: int, max_retries: int = 3) -> pd.DataFrame:
    client = authorize_gsheets()
    for attempt in range(1, max_retries + 1):
        try:
            ws = client.open_by_key(sheet_id).get_worksheet_by_id(gid)
            records = ws.get_all_records()
            return pd.DataFrame(records)
        except APIError as e:
            # если именно 503 — пробуем снова
            if hasattr(e, 'response') and getattr(e.response, 'status_code', None) == 503 and attempt < max_retries:
                wait = 2 ** attempt
                st.warning(f"Google API вернул 503, пробую снова через {wait}s (попытка {attempt}/{max_retries})…")
                time.sleep(wait)
                continue
            # иначе — выбрасываем
            raise

SHEET_ID = "1xqGCXsebSmYL4bqAwvTmD9lOentI45CTMxhea-ZDFls"
GID      = 1731969866

try:
    df = load_sheet_with_retry(SHEET_ID, GID)
except Exception as e:
    st.error(f"Ошибка авторизации или загрузки данных: {e}")
    st.stop()

# Фильтрация C == 'active'
if "C" in df.columns:
    df = df[df["C"].astype(str).str.lower() == "active"]
else:
    st.warning("Колонка 'C' не найдена в таблице.")

# Оставляем только A, B, P, Q, V
wanted = ["A", "B", "P", "Q", "V"]
cols = [c for c in wanted if c in df.columns]
if not cols:
    st.error("Ни одна из колонок A, B, P, Q, V не найдена.")
    st.stop()
df = df[cols]

# Сайдбар: мульти-фильтрация
st.sidebar.header("Filters")
for col in cols:
    choices = sorted(df[col].dropna().unique())
    sel = st.sidebar.multiselect(col, choices)
    if sel:
        df = df[df[col].isin(sel)]

# Показ AgGrid
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(filterable=True, sortable=True, resizable=True)
grid_options = gb.build()

AgGrid(df, gridOptions=grid_options, height=500, fit_columns_on_grid_load=True)
st.write(f"Всего строк: {len(df)}")

# Экспорт в Excel
@st.cache_data
def to_excel(data: pd.DataFrame):
    return data.to_excel(index=False)

if st.button("Export to Excel"):
    xlsx = to_excel(df)
    st.download_button("Download XLSX", xlsx, file_name="report.xlsx")
