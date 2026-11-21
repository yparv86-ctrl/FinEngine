import sys
sys.path.append("src")

import streamlit as st
from finenginepy.db import get_valuation_history, clear_valuation_history, require_auth

st.set_page_config(page_title="Audit Ledger | FinEngine", layout="wide")

# --- Private Wealth Gold Glassmorphism & Typography ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    .stApp {
        background: radial-gradient(circle at 15% 10%, rgba(245, 158, 11, 0.06), transparent 38%),
                    radial-gradient(circle at 85% 20%, rgba(156, 163, 175, 0.04), transparent 42%),
                    #0C0C0E !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    [data-testid="stSidebar"] {
        background: rgba(22, 22, 26, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }

    [data-testid="stDataFrame"], [data-testid="stVerticalBlockBorderWrapper"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-variant-numeric: tabular-nums !important;
        background: rgba(22, 22, 26, 0.72) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 12px !important;
    }

    button[kind="primary"] {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0C0C0E !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <h1 style="margin-bottom: 0px; font-weight: 700; letter-spacing: -0.5px;">
        FinEngine <span style="color: #F59E0B; font-weight: 400;">| Valuation Audit Ledger</span>
    </h1>
    <p style="color: #9CA3AF; font-size: 1.0rem; margin-top: 4px; margin-bottom: 24px;">
        Encrypted cloud history of your intrinsic valuation runs.
    </p>
""", unsafe_allow_html=True)

require_auth()

with st.container(border=True):
    history_df = get_valuation_history()

    if not history_df.empty:
        st.dataframe(
            history_df.style.format({
                "market_price": "${:.2f}",
                "intrinsic_value": "${:.2f}",
                "discount_rate": "{:.2%}",
                "spread_pct": "{:+.1f}%"
            }),
            use_container_width=True,
            hide_index=True
        )
        col_btn, _ = st.columns([1, 4])
        with col_btn:
            if st.button("Purge Audit Ledger", type="secondary", use_container_width=True):
                clear_valuation_history()
                st.rerun()
    else:
        st.caption("No historical valuations logged under this account yet. Run a valuation on the main terminal to populate your ledger.")