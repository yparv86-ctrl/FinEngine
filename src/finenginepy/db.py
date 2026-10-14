import pandas as pd
import streamlit as st
from supabase import create_client, Client

# Initialize Supabase client securely using Streamlit Secrets
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_connection()

# Temporary dummy user ID until we build the Auth UI in the next step
GUEST_USER_ID = "00000000-0000-0000-0000-000000000000"

def init_db():
    # SQLite initialization is no longer needed. 
    # We keep this empty function so app.py doesn't crash on import.
    pass

def log_valuation(ticker, model_type, market_price, intrinsic_value, discount_rate):
    data = {
        "user_id": GUEST_USER_ID,
        "ticker": ticker,
        "model_type": model_type,
        "market_price": float(market_price),
        "intrinsic_value": float(intrinsic_value),
        "discount_rate": float(discount_rate)
    }
    # Insert directly into the cloud database
    supabase.table("audit_ledger").insert(data).execute()

def get_valuation_history():
    # Fetch only the current user's data from the cloud
    response = supabase.table("audit_ledger").select("*").eq("user_id", GUEST_USER_ID).execute()
    data = response.data
    
    if not data:
        return pd.DataFrame()
    
    # Convert to DataFrame and format to match our original UI structure
    df = pd.DataFrame(data)
    df = df.rename(columns={"created_at": "timestamp"})
    
    # Re-calculate spread and verdict for the UI
    df['spread_pct'] = ((df['intrinsic_value'] - df['market_price']) / df['market_price']) * 100
    df['verdict'] = df.apply(lambda row: "UNDERVALUED" if row['intrinsic_value'] > row['market_price'] else "OVERVALUED", axis=1)
    
    # Format timestamps cleanly
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
    
    return df[['timestamp', 'ticker', 'model_type', 'market_price', 'intrinsic_value', 'discount_rate', 'spread_pct', 'verdict']]

def clear_valuation_history():
    # Deletes only the current user's cloud records
    supabase.table("audit_ledger").delete().eq("user_id", GUEST_USER_ID).execute()