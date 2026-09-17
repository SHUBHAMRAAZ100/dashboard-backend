"""
Simulation -> Fixed -> Highlight Tracker (API-connected version)
------------------------------------------------------------------
This version does NOT read the CSV directly. It fetches data from the
backend API (main.py) over HTTP -- the way a real frontend/backend split works.

HOW TO RUN:
1. Start the backend first, in its own terminal:
     cd backend
     pip install fastapi uvicorn pandas
     uvicorn main:app --reload
   Leave that terminal running.

2. In a SECOND terminal, run this dashboard:
     pip install streamlit requests
     streamlit run dashboard_app_api.py

3. If you deploy the backend to Render, change API_BASE_URL below to your
   Render URL (e.g. "https://your-app-name.onrender.com") instead of localhost.
"""

import pandas as pd
import requests
import streamlit as st

API_BASE_URL = "https://dashboard-backend-7pgp.onrender.com"   # change this to your Render URL after deploying
MONTHS = ["April", "May", "June", "July"]

st.set_page_config(page_title="Simulation Cycle Dashboard", layout="wide")


@st.cache_data(ttl=30)
def fetch_summary(month):
    r = requests.get(f"{API_BASE_URL}/api/summary/{month}", timeout=10)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=30)
def fetch_departments(month):
    r = requests.get(f"{API_BASE_URL}/api/departments/{month}", timeout=10)
    r.raise_for_status()
    return pd.DataFrame(r.json()).set_index("Department")


@st.cache_data(ttl=30)
def fetch_trend():
    r = requests.get(f"{API_BASE_URL}/api/trend", timeout=10)
    r.raise_for_status()
    return pd.DataFrame(r.json()).T


# ---------- Try connecting to the API first (allow extra time for Render cold start) ----------
try:
    with st.spinner("Connecting to backend (may take up to a minute if it was asleep)..."):
        requests.get(f"{API_BASE_URL}/", timeout=60).raise_for_status()
except Exception:
    st.error(
        f"Can't reach the backend API at {API_BASE_URL}. "
        "Make sure main.py (uvicorn) is running, or update API_BASE_URL to your Render link."
    )
    st.stop()

# ---------- Header ----------
st.markdown("##### PROCESS CYCLE DASHBOARD")
st.title("Simulation → Fixed → Highlight Tracker")
st.caption(
    "A simulated employee enters a 2-month cooldown. If not Fixed, they're barred for good. "
    "If Fixed, they return after cooldown — and a Fixed return gets Highlighted. "
    f"Data is fetched live from the API at {API_BASE_URL}."
)
st.divider()

# ---------- Month selector + View button ----------
col_a, col_b = st.columns([2, 3])
with col_a:
    selected_month = st.selectbox("Choose a month", MONTHS, index=0)
    view_clicked = st.button("View", type="primary")

if "shown_month" not in st.session_state:
    st.session_state.shown_month = MONTHS[0]
if view_clicked:
    st.session_state.shown_month = selected_month

shown_month = st.session_state.shown_month
with col_b:
    st.markdown(f"Showing results for **{shown_month}**")

st.write("")

# ---------- Big stat cards (from API) ----------
summary = fetch_summary(shown_month)

c1, c2, c3 = st.columns(3)
c1.metric("Simulated", f"{summary['simulated']:,}")
c2.metric("Fixed", f"{summary['fixed']:,}",
          f"{(summary['fixed'] / max(summary['simulated'], 1)) * 100:.1f}% of simulated")
c3.metric("Highlighted", f"{summary['highlighted']:,}", "returned & fixed again")

c4, c5, c6 = st.columns(3)
c4.metric("Reported", f"{summary['reported']:,}")
c5.metric("Trapped", f"{summary['trapped']:,}")
c6.metric("Barred to date", f"{summary['barred']:,}")

st.write("")
st.subheader(f"Department breakdown — {shown_month}")
st.dataframe(fetch_departments(shown_month), width='stretch')

st.write("")
st.subheader("Monthly Trendline (April → July)")
trend_df = fetch_trend().reindex(MONTHS)[["simulated", "fixed", "highlighted"]].rename(
    columns={"simulated": "Simulated", "fixed": "Fixed", "highlighted": "Highlighted"}
)
st.line_chart(trend_df)
