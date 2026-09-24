import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

from finenginepy.data_fetcher import fetch_raw_data, clean_financials
from finenginepy.dcf_model import load_macro_assumptions, calculate_wacc, run_dcf_valuation
from finenginepy.ddm_model import run_ddm_valuation
from finenginepy.guards import validate_company, ValuationError
from finenginepy.pipeline import generate_pdf_report
from finenginepy.sensitivity import build_sensitivity_matrix

st.set_page_config(page_title="FinEngine | Dual-Model Platform", layout="wide")

st.title("📊 FinEngine: Dual-Model Valuation Platform")
st.markdown("Institutional-grade 3-Stage DCF and Dividend Discount Models with automated routing.")

# --- Sidebar: User Inputs ---
st.sidebar.header("Model Controls")
ticker_input = st.sidebar.text_input("Stock Ticker", value="JPM").upper().strip()

st.sidebar.subheader("DCF Levers (Tech/Industrials)")
short_term_growth = st.sidebar.slider("Stage 1: High Growth Rate", min_value=-0.10, max_value=0.40, value=0.08, step=0.01)
perpetual_growth = st.sidebar.slider("Stage 3: Terminal Growth", min_value=0.01, max_value=0.04, value=0.025, step=0.0025)

st.sidebar.subheader("DDM Levers (Banks)")
div_growth_rate = st.sidebar.slider("Dividend Growth Rate", min_value=0.01, max_value=0.15, value=0.06, step=0.01)

run_btn = st.sidebar.button("Run Intrinsic Valuation", type="primary")

if run_btn:
    try:
        with st.spinner(f"Ingesting ledgers and validating {ticker_input}..."):
            inc, bal, cf, info = fetch_raw_data(ticker_input)
            clean_data = clean_financials(inc, bal, cf)
            
            # The router decides the fate
            model_route = validate_company(info, clean_data)
            macro = load_macro_assumptions()
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))

            # Execute routed model
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

        # --- Top KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Market Price", f"${current_price:.2f}")
        col2.metric("Intrinsic Value", f"${intrinsic_val:.2f}")
        col3.metric("Discount Rate (WACC / r_e)", f"{cost_of_capital*100:.2f}%")
        
        spread = ((intrinsic_val - current_price) / current_price) * 100 if current_price else 0
        verdict = "UNDERVALUED" if intrinsic_val > current_price else "OVERVALUED"
        col4.metric("Spread / Verdict", f"{spread:.1f}%", delta=verdict)

        st.divider()

        # --- Middle Row: Historical Visuals ---
        mid_col1, mid_col2 = st.columns([1, 1])

        with mid_col1:
            st.subheader("Historical Cash Performance")
            plot_df = clean_data.dropna()
            dates = [str(d).split(' ')[0] for d in plot_df.index]
            
            fig, ax = plt.subplots(figsize=(6, 4))
            x = range(len(dates))
            w = 0.35
            ax.bar([i - w/2 for i in x], plot_df['Revenue'] / 1e9, w, label="Revenue", color="#1f77b4")
            ax.bar([i + w/2 for i in x], plot_df['Free Cash Flow'] / 1e9, w, label="Free Cash Flow", color="#2ca02c")
            ax.set_ylabel("Billions (USD)")
            ax.set_xticks(x)
            ax.set_xticklabels(dates)
            ax.legend()
            st.pyplot(fig)

        with mid_col2:
            if model_route == "DCF":
                st.subheader("Valuation Multiverse (Sensitivity)")
                matrix_df = build_sensitivity_matrix(clean_data, info, cost_of_capital, base_g=perpetual_growth, short_term_growth=short_term_growth)
                st.dataframe(matrix_df.style.highlight_max(axis=None, color='#2ca02c33'), use_container_width=True)
            else:
                st.subheader("Dividend Policy Analysis")
                base_div = info.get('dividendRate') or info.get('trailingAnnualDividendRate', 0)
                st.markdown(f"**Base Dividend:** ${base_div:.2f}")
                st.markdown(f"**Payout Ratio:** {info.get('payoutRatio', 0)*100:.1f}%")
                st.markdown("*Note: Sensitivity matrix is currently optimized for FCFF (DCF). DDM sensitivity expansion coming in Week 2.*")

        st.divider()

        # --- Bottom Row: PDF Generation ---
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