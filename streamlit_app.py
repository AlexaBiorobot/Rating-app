import streamlit as st
import json
import pandas as pd
from st_aggrid import GridOptionsBuilder, AgGrid
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Live Google Sheet Table", layout="wide")
st.title("Live Google Sheet Table with Filters (Authorized)")

# ————————————————————————————————————————————————
# 1) Авторизация через сервисный аккаунт
# ————————————————————————————————————————————————

def authorize_gsheets():
    # Проверяем, что секрет есть
    if "GCP_SERVICE_ACCOUNT" not in st.secrets:
        st.error("Секрет GCP_SERVICE_ACCOUNT не найден. Добавьте его в Settings → Secrets или в .streamlit/secrets.toml")
        st.stop()

    # Парсим JSON-строку
    try:
        sa_info = json.loads(st.secrets["GCP_SERVICE_ACCOUNT"])
    except json.JSONDecodeError as e:
        st.error(f"Не получилось распарсить JSON из GCP_SERVICE_ACCOUNT: {e}")
        st.stop()

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly"
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    return gspread.authorize(creds)

# ————————————————————————————————————————————————
# 2) Загрузка данных
# ————————————————————————————————————————————————

@st.cache_data(ttl=600)
def load_sheet(sheet_id: str, gid: int) -> pd.DataFrame:
    client = authorize_gsheets()
    ws = client.open_by_key(sheet_id).get_worksheet_by_id(gid)
    records = ws.get_all_records()
    return pd.DataFrame(records)

SHEET_ID = "1xqGCXsebSmYL4bqAwvTmD9lOentI45CTMxhea-ZDFls"
GID      = 1731969866

try:
    df = load_sheet(SHEET_ID, GID)
except Exception as e:
    st.error(f"Ошибка авторизации или загрузки данных: {e}")
    st.stop()

# ————————————————————————————————————————————————
# 3) Фильтрация и отображение
# ————————————————————————————————————————————————

# Оставляем только где C == 'active'
if "C" in df.columns:
    df = df[df["C"].astype(str).str.lower() == "active"]
else:
    st.warning("Колонка 'C' не найдена в таблице.")

# Выбираем колонки A, B, P, Q, V
wanted = ["A", "B", "P", "Q", "V"]
cols = [c for c in wanted if c in df.columns]
if not cols:
    st.error("Ни одна из колонок A, B, P, Q, V не найдена.")
    st.stop()
df = df[cols]

# Сайдбар: мультивыбор для всех этих колонок
st.sidebar.header("Filters")
for col in cols:
    vals = sorted(df[col].dropna().unique())
    sel = st.sidebar.multiselect(col, vals)
    if sel:
        df = df[df[col].isin(sel)]

# AgGrid для интерактивной таблицы
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(filterable=True, sortable=True, resizable=True)
grid_options = gb.build()

AgGrid(
    df,
    gridOptions=grid_options,
    height=500,
    fit_columns_on_grid_load=True
)

st.write(f"Всего строк: {len(df)}")

# Кнопка экспорта
@st.cache_data
def to_excel(data: pd.DataFrame):
    return data.to_excel(index=False)

if st.button("Export to Excel"):
    xlsx = to_excel(df)
    st.download_button("Download XLSX", xlsx, file_name="report.xlsx")
