"""
Backend API for the Simulation -> Fixed -> Highlight dashboard.

WHAT THIS IS:
- A database table (SQLite: employees.db, table "employees") built from the CSV.
- A REST API (FastAPI) that serves summary data FROM that table.
- Middleware that logs every request and times how long it took.

HOW TO RUN LOCALLY:
1. pip install fastapi uvicorn pandas
2. Make sure "employees.db" is in the same folder (run build_database.py first if not).
3. In terminal: uvicorn main:app --reload
4. Open http://127.0.0.1:8000/docs to see and test every endpoint in the browser.

HOW TO DEPLOY ON RENDER:
See the render_deploy_steps.txt file in this same folder.
"""

import sqlite3
import time
import logging

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard-api")

DB_PATH = "employees.db"
MONTHS = ["April", "May", "June", "July"]

app = FastAPI(title="Simulation Cycle Dashboard API")

# ---------- Middleware #1: allow the dashboard (running elsewhere) to call this API ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # for a class project, allow all; tighten this in real production use
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Middleware #2: log every request + how long it took ----------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms:.1f}ms)")
    return response


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def validate_month(month: str):
    if month not in MONTHS:
        raise HTTPException(status_code=400, detail=f"month must be one of {MONTHS}")


# ---------- Routes ----------

@app.get("/")
def root():
    return {"status": "ok", "message": "Dashboard API is running. See /docs for endpoints."}


@app.get("/api/months")
def list_months():
    return {"months": MONTHS}


@app.get("/api/summary/{month}")
def month_summary(month: str):
    validate_month(month)
    conn = get_connection()
    row = conn.execute(f"""
        SELECT
            SUM("{month}_Simulation") AS simulated,
            SUM("{month}_Fixed") AS fixed,
            SUM("{month}_Reported") AS reported,
            SUM("{month}_Trapped") AS trapped,
            SUM("{month}_Highlighted") AS highlighted,
            SUM("{month}_Barred") AS barred
        FROM employees
    """).fetchone()
    conn.close()
    return dict(row)


@app.get("/api/departments/{month}")
def department_breakdown(month: str):
    validate_month(month)
    conn = get_connection()
    rows = conn.execute(f"""
        SELECT
            Department,
            SUM("{month}_Simulation") AS simulated,
            SUM("{month}_Fixed") AS fixed,
            SUM("{month}_Highlighted") AS highlighted
        FROM employees
        GROUP BY Department
        ORDER BY Department
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/trend")
def monthly_trend():
    conn = get_connection()
    result = {}
    for m in MONTHS:
        row = conn.execute(f"""
            SELECT
                SUM("{m}_Simulation") AS simulated,
                SUM("{m}_Fixed") AS fixed,
                SUM("{m}_Highlighted") AS highlighted
            FROM employees
        """).fetchone()
        result[m] = dict(row)
    conn.close()
    return result
