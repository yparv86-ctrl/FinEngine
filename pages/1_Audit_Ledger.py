import sys
sys.path.append("src")
import streamlit as st
from finenginepy.db import get_valuation_history, clear_valuation_history

st.set_page_config(page_title="Audit Ledger | FinEngine", layout="wide")

# Apply our global typography and styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.title("📑 Valuation Audit Ledger")
st.caption("Persistent SQLite database of all historical intrinsic value calculations.")

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
        height=600
    )
    
    col1, col2 = st.columns(2)
    with col1:
        csv_bytes = history_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Ledger (CSV)",
            data=csv_bytes,
            file_name="finengine_valuation_audit_ledger.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col2:
        if st.button("🗑️ Purge Audit Ledger", use_container_width=True):
            clear_valuation_history()
            st.rerun()
else:
    st.info("The audit ledger is currently empty. Run a valuation on the main engine to log data.")