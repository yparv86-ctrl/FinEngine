import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "valuations_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS valuation_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            ticker TEXT,
            model_type TEXT,
            market_price REAL,
            intrinsic_value REAL,
            discount_rate REAL,
            spread_pct REAL,
            verdict TEXT
        )
    """)
    conn.commit()
    conn.close()

def log_valuation(ticker, model_type, market_price, intrinsic_value, discount_rate):
    spread = ((intrinsic_value - market_price) / market_price) * 100 if market_price else 0.0
    verdict = "UNDERVALUED" if intrinsic_value > market_price else "OVERVALUED"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO valuation_runs 
        (timestamp, ticker, model_type, market_price, intrinsic_value, discount_rate, spread_pct, verdict)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (timestamp, ticker, model_type, market_price, intrinsic_value, discount_rate, spread, verdict))
    conn.commit()
    conn.close()

def get_valuation_history():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT timestamp, ticker, model_type, market_price, intrinsic_value, discount_rate, spread_pct, verdict FROM valuation_runs ORDER BY id DESC", conn)
    conn.close()
    return df