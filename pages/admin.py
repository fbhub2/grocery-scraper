import sys
import sqlite3
from pathlib import Path
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
import db
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env", override=True)
_ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")

st.set_page_config(page_title="Admin", page_icon="🔧", layout="wide")

_user = auth.require_login()

if _user.get("email") != _ADMIN_EMAIL:
    st.error("Ingen tilgang.")
    st.stop()

st.title("🔧 Admin")

# ---------------------------------------------------------------------------
# Oversikt
# ---------------------------------------------------------------------------

conn = sqlite3.connect(db.DB_PATH)
conn.row_factory = sqlite3.Row


def _count(table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _df(sql: str, params: tuple = ()) -> pd.DataFrame:
    rows = conn.execute(sql, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows]) if rows else pd.DataFrame()


st.subheader("Oversikt")
cols = st.columns(6)
for col, (label, table) in zip(cols, [
    ("Brukere", "user"),
    ("Produkter", "product"),
    ("Normnavn", "normal"),
    ("Prishistorikk", "product_price_history"),
    ("Watchlist", "watchlist"),
    ("Sesjoner", "session"),
]):
    col.metric(label, _count(table))

st.divider()

# ---------------------------------------------------------------------------
# Brukere
# ---------------------------------------------------------------------------

st.subheader("Brukere")
users_df = _df("SELECT id, email, name, created_at FROM user ORDER BY created_at DESC")
if not users_df.empty:
    st.dataframe(users_df, use_container_width=True, hide_index=True)
else:
    st.caption("Ingen brukere")

# ---------------------------------------------------------------------------
# Aktive sesjoner
# ---------------------------------------------------------------------------

st.subheader("Aktive sesjoner")
sessions_df = _df(
    """SELECT s.created_at, u.email, u.name,
              substr(s.token, 1, 8) || '...' as token_prefix
       FROM session s
       LEFT JOIN (
           SELECT json_extract(user_json,'$.email') as email,
                  json_extract(user_json,'$.name') as name,
                  token
           FROM session
       ) u ON u.token = s.token
       ORDER BY s.created_at DESC LIMIT 20"""
)
if not sessions_df.empty:
    st.dataframe(sessions_df, use_container_width=True, hide_index=True)
else:
    st.caption("Ingen sesjoner")

# ---------------------------------------------------------------------------
# Rådata — valgfri tabell
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Rådata")

all_tables = [r[0] for r in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()]

chosen = st.selectbox("Velg tabell", all_tables)
limit = st.slider("Maks rader", 10, 500, 50)

if chosen:
    df = _df(f"SELECT * FROM {chosen} ORDER BY rowid DESC LIMIT ?", (limit,))
    if not df.empty:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} rader (maks {limit})")
    else:
        st.caption("Tom tabell")

# ---------------------------------------------------------------------------
# Vedlikehold
# ---------------------------------------------------------------------------

st.divider()
st.subheader("Vedlikehold")

col1, col2 = st.columns(2)
with col1:
    if st.button("Slett utlopte sesjoner (eldre enn 30 dager)", type="secondary"):
        conn.execute("DELETE FROM session WHERE created_at < date('now', '-30 days')")
        conn.commit()
        st.success("Utlopte sesjoner slettet")

with col2:
    n_normals = _count("normal")
    st.metric("Normal-navn uten auto_name", conn.execute(
        "SELECT COUNT(*) FROM normal WHERE auto_name IS NULL"
    ).fetchone()[0])

conn.close()
