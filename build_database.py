"""
Run this once to build employees.db from the CSV.
Usage:  python build_database.py
"""
import pandas as pd
import sqlite3

CSV_PATH = "employee_process_simulation_RULES_apr_jul.csv"
DB_PATH = "employees.db"

df = pd.read_csv(CSV_PATH)
conn = sqlite3.connect(DB_PATH)
df.to_sql("employees", conn, if_exists="replace", index=False)
conn.close()

print(f"Built {DB_PATH} with {len(df):,} rows in table 'employees'.")
