import sys
sys.path.append("src")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

from finenginepy.data_fetcher import fetch_raw_data, clean_financials
from finenginepy.dcf_model import load_macro_assumptions, calculate_wacc, run_dcf_valuation
from finenginepy.ddm_model import run_ddm_valuation
from finenginepy.guards import validate_company, ValuationError
from finenginepy.pipeline import generate_pdf_report
from finenginepy.sensitivity import build_sensitivity_matrix, build_ddm_sensitivity_matrix
from finenginepy.db import init_db, log_valuation

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="FinEngine | Valuation Platform", layout="wide", initial_sidebar_state="expanded")

# Initialize local database
init_db()

# --- Core Data Caching Pipeline ---
@st.cache_data(ttl=3600)
def load_and_cache_data(ticker):
    inc, bal, cf, info = fetch_raw_data(ticker)
    clean_data = clean_financials(inc, bal, cf)
    return info, clean_data

# --- UI Overhaul: Custom CSS Injection & Typography ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    [data-testid="stMetric"] {
        background-color: #171821;
        border-left: 3px solid #00FFCC;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.4);
    }
    
    button[kind="primary"] {
        background-color: #00FFCC !important;
        color: #0b0f19 !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        border: none !important;
        border-radius: 6px !important;
        transition: all 0.3s ease-in-out !important;
        box-shadow: 0 0 8px rgba(0, 255, 204, 0.2) !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 0 18px rgba(0, 255, 204, 0.6) !important;
        transform: translateY(-2px) !important;
    }
    </style>
""", unsafe_allow_html=True)

# Sleek Custom Header
st.markdown("""
    <h1 style='font-family: "Inter", sans-serif; font-weight: 700; letter-spacing: -1.2px; margin-bottom: 0px;'>
        FinEngine <span style='color: #00FFCC; font-weight: 400;'>| Enterprise Valuation</span>
    </h1>
    <p style='color: #8b92a5; font-size: 1.05rem; margin-top: 5px; margin-bottom: 25px;'>
        Institutional-grade 3-Stage DCF and Dividend Discount Models with automated routing.
    </p>
""", unsafe_allow_html=True)

# --- Sidebar: Controls ---
st.sidebar.header("Model Controls")
ticker_input = st.sidebar.text_input("Stock Ticker", value="AAPL").upper().strip()

st.sidebar.subheader("DCF Levers (Tech/Industrials)")
short_term_growth = st.sidebar.slider("Stage 1: High Growth Rate", min_value=-0.10, max_value=0.40, value=0.08, step=0.01)
perpetual_growth = st.sidebar.slider("Stage 3: Terminal Growth", min_value=0.01, max_value=0.04, value=0.025, step=0.0025)

st.sidebar.subheader("DDM Levers (Banks)")
div_growth_rate = st.sidebar.slider("Dividend Growth Rate", min_value=0.01, max_value=0.15, value=0.06, step=0.01)

run_btn = st.sidebar.button("Run Intrinsic Valuation", type="primary")

if run_btn:
    try:
        with st.spinner(f"Ingesting ledgers and validating {ticker_input}..."):
            info, clean_data = load_and_cache_data(ticker_input)
            model_route = validate_company(info, clean_data)
            macro = load_macro_assumptions()
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))

            if model_route == "DDM":
                st.info("🏦 Financial Institution Detected: Routed to Dividend Discount Model (DDM)")
                intrinsic_val, cost_of_capital = run_ddm_valuation(
                    info, macro, forecast_years=5, 
                    dividend_growth_rate=div_growth_rate, 
                    terminal_growth_rate=perpetual_growth
                )
            else:
                st.info("🏭 Standard Corporate Detected: Routed to 3-Stage DCF Model")
                cost_of_capital, mkt_cap, debt = calculate_wacc(info, macro)
                intrinsic_val = run_dcf_valuation(clean_data, info, macro, cost_of_capital, mkt_cap, debt)

            # Persist to SQLite ledger
            log_valuation(ticker_input, model_route, current_price, intrinsic_val, cost_of_capital)

        # --- Top KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Market Price", f"${current_price:.2f}")
        col2.metric("Intrinsic Value", f"${intrinsic_val:.2f}")
        col3.metric("Discount Rate", f"{cost_of_capital*100:.2f}%")
        
        spread = ((intrinsic_val - current_price) / current_price) * 100 if current_price else 0
        verdict = "UNDERVALUED" if intrinsic_val > current_price else "OVERVALUED"
        col4.metric("Spread / Verdict", f"{spread:.1f}%", delta=verdict)

        st.divider()

        # --- Middle Row: Visuals & Sensitivity ---
        mid_col1, mid_col2 = st.columns([1, 1])

        with mid_col1:
            st.subheader("Historical Cash Performance")
            plot_df = clean_data.dropna(subset=['Revenue', 'Free Cash Flow'])
            dates = [str(d).split(' ')[0] for d in plot_df.index]
            
            fig, ax = plt.subplots(figsize=(6, 3.2))
            x = range(len(dates))
            w = 0.35
            ax.bar([i - w/2 for i in x], plot_df['Revenue'] / 1e9, w, label="Revenue", color="#1f77b4")
            ax.bar([i + w/2 for i in x], plot_df['Free Cash Flow'] / 1e9, w, label="Free Cash Flow", color="#2ca02c")
            ax.set_ylabel("Billions (USD)")
            ax.set_xticks(x)
            ax.set_xticklabels(dates)
            ax.legend()
            st.pyplot(fig)

            # --- Multi-Ratio Health Trends ---
            st.subheader("Operating Efficiency & Capital Ratios")
            ratio_tab1, ratio_tab2, ratio_tab3 = st.tabs(["FCF Margin", "Net Margin", "ROIC"])
            
            with ratio_tab1:
                fcf_margin = pd.DataFrame({
                    'Date': dates,
                    'FCF Margin (%)': (plot_df['Free Cash Flow'] / plot_df['Revenue']) * 100
                }).set_index('Date')
                st.line_chart(fcf_margin, color="#ff7f0e", height=190)

            with ratio_tab2:
                net_margin = pd.DataFrame({
                    'Date': dates,
                    'Net Profit Margin (%)': (plot_df['Net Income'] / plot_df['Revenue']) * 100
                }).set_index('Date')
                st.line_chart(net_margin, color="#2ca02c", height=190)

            with ratio_tab3:
                if 'Invested Capital' in plot_df.columns and plot_df['Invested Capital'].isna().sum() == 0:
                    tax_rate = macro.get("default_tax_rate", 0.21)
                    nopat = plot_df['Operating Income'] * (1 - tax_rate)
                    roic_series = (nopat / plot_df['Invested Capital']) * 100
                    roic_df = pd.DataFrame({'Date': dates, 'ROIC (%)': roic_series}).set_index('Date')
                    st.line_chart(roic_df, color="#1f77b4", height=190)
                else:
                    st.caption("Invested capital structure not applicable or missing for this ticker.")

        with mid_col2:
            if model_route == "DCF":
                st.subheader("Valuation Multiverse (Sensitivity)")
                matrix_df = build_sensitivity_matrix(
                    clean_data, info, cost_of_capital, 
                    base_g=perpetual_growth, 
                    short_term_growth=short_term_growth
                )
                st.dataframe(matrix_df.style.highlight_max(axis=None, color='#2ca02c33'), use_container_width=True)
            else:
                st.subheader("Dividend Policy Analysis")
                base_div = info.get('dividendRate') or info.get('trailingAnnualDividendRate', 0)
                c_div1, c_div2 = st.columns(2)
                c_div1.metric("Base Dividend (DPS)", f"${base_div:.2f}")
                c_div2.metric("Payout Ratio", f"{info.get('payoutRatio', 0)*100:.1f}%")
                
                st.subheader("DDM Valuation Multiverse")
                ddm_matrix = build_ddm_sensitivity_matrix(
                    info, 
                    cost_of_capital, 
                    div_growth_rate=div_growth_rate, 
                    base_terminal_g=perpetual_growth
                )
                if not ddm_matrix.empty:
                    st.dataframe(
                        ddm_matrix.style.highlight_max(axis=None, color='#2ca02c33').format("${:.2f}", na_rep="N/A"), 
                        use_container_width=True
                    )
                else:
                    st.caption("Unable to compute sensitivity matrix: Missing or non-positive dividend baseline.")

        st.divider()

        # --- Bottom Section: Export Tear-Sheet ---
        st.subheader("Institutional Deliverables")
        chart_file = f"{ticker_input}_financials.png"
        fig.savefig(chart_file, dpi=200, bbox_inches='tight')
        generate_pdf_report(ticker_input, current_price, intrinsic_val, cost_of_capital, chart_file)
        
        pdf_path = f"{ticker_input}_Valuation_Report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_data:
                st.download_button(
                    label=f"📥 Download {ticker_input} Executive PDF Tear-Sheet",
                    data=pdf_data,
                    file_name=pdf_path,
                    mime="application/pdf"
                )

    except ValuationError as ve:
        st.error(str(ve))
    except Exception as e:
        st.error(f"Execution Error: {e}")