import os
import sys

sys.path.append("src")

import matplotlib.pyplot as plt
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from finenginepy.comps import run_peer_comps
from finenginepy.data_fetcher import clean_financials, fetch_raw_data
from finenginepy.db import init_db, log_valuation, require_auth
from finenginepy.dcf_model import calculate_wacc, load_macro_assumptions, run_dcf_valuation
from finenginepy.ddm_model import run_ddm_valuation
from finenginepy.guards import ValuationError, validate_company
from finenginepy.pipeline import generate_pdf_report
from finenginepy.sensitivity import build_ddm_sensitivity_matrix, build_sensitivity_matrix

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title="FinEngine | Valuation Platform",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database hook
init_db()


# --- Core Data Caching Pipeline ---
@st.cache_data(ttl=3600)
def load_and_cache_data(ticker: str) -> tuple[dict, pd.DataFrame]:
    fetched = fetch_raw_data(ticker)
    if fetched is None:
        raise ValueError(f"Could not fetch market data for {ticker}.")
    inc, bal, cf, info = fetched
    clean_data = clean_financials(inc, bal, cf)
    return info, clean_data


@st.cache_data(ttl=3600)
def load_cached_comps(
    ticker: str,
    info: dict,
    custom_peers_tuple: tuple[str, ...]
) -> tuple[pd.DataFrame, dict]:
    peer_list = list(custom_peers_tuple) if custom_peers_tuple else None
    return run_peer_comps(ticker, info, peer_list)


# --- Phase 3: Private Wealth Gold Glassmorphism & Typography ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Warm Carbon Background with Ambient Champagne Glow */
    .stApp {
        background: radial-gradient(circle at 15% 10%, rgba(245, 158, 11, 0.06), transparent 38%),
                    radial-gradient(circle at 85% 20%, rgba(156, 163, 175, 0.04), transparent 42%),
                    #0C0C0E !important;
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Frosted Graphite Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(22, 22, 26, 0.85) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06) !important;
    }

    /* Graphite Glass Metric Cards with Champagne Amber Top Border */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(22, 22, 26, 0.92) 0%, rgba(22, 22, 26, 0.65) 100%) !important;
        backdrop-filter: blur(14px) !important;
        -webkit-backdrop-filter: blur(14px) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-top: 1px solid rgba(245, 158, 11, 0.45) !important;
        padding: 18px 22px !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.55) !important;
        transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), border-color 0.25s ease, box-shadow 0.25s ease !important;
    }
    [data-testid="stMetric"]:hover {
        transform: translateY(-4px) !important;
        border-color: rgba(245, 158, 11, 0.65) !important;
        box-shadow: 0 12px 34px rgba(245, 158, 11, 0.12) !important;
    }

    /* Soft Silver Labels & Monospace Financial Numbers */
    [data-testid="stMetricLabel"], label {
        color: #9CA3AF !important;
        font-size: 0.80rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.9px !important;
        font-weight: 600 !important;
    }
    [data-testid="stMetricValue"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-variant-numeric: tabular-nums !important;
        color: #F9FAFB !important;
        font-weight: 700 !important;
        letter-spacing: -0.5px !important;
    }
    [data-testid="stMetricDelta"], [data-testid="stDataFrame"] {
        font-family: 'JetBrains Mono', monospace !important;
        font-variant-numeric: tabular-nums !important;
    }

    /* Graphite Bento-Grid Containers, Tables & Alerts */
    [data-testid="stDataFrame"], [data-testid="stAlert"], [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(22, 22, 26, 0.72) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 12px !important;
    }

    /* Champagne Amber Primary Action Button */
    button[kind="primary"] {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%) !important;
        color: #0C0C0E !important;
        font-weight: 700 !important;
        letter-spacing: 0.4px !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1) !important;
        box-shadow: 0 4px 14px rgba(245, 158, 11, 0.22) !important;
    }
    button[kind="primary"]:hover {
        box-shadow: 0 6px 22px rgba(245, 158, 11, 0.45) !important;
        transform: translateY(-2px) scale(1.01) !important;
    }

    /* Institutional Champagne Status Pill */
    .model-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(245, 158, 11, 0.10);
        border: 1px solid rgba(245, 158, 11, 0.30);
        color: #F59E0B;
        padding: 6px 14px;
        border-radius: 999px;
        font-size: 0.76rem;
        font-weight: 600;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        margin-bottom: 18px;
    }
    .status-dot {
        width: 7px;
        height: 7px;
        background-color: #F59E0B;
        border-radius: 50%;
        box-shadow: 0 0 8px #F59E0B;
    }
    </style>
""", unsafe_allow_html=True)

# Sleek Custom Header
st.markdown("""
    <h1 style="margin-bottom: 0px; font-weight: 700; letter-spacing: -0.5px;">
        FinEngine <span style="color: #F59E0B; font-weight: 400;">| Enterprise Valuation</span>
    </h1>
    <p style="color: #9CA3AF; font-size: 1.0rem; margin-top: 4px; margin-bottom: 24px;">
        Institutional-grade 3-Stage DCF and Dividend Discount Models with automated routing.
    </p>
""", unsafe_allow_html=True)

require_auth()

# --- Sidebar: Controls ---
st.sidebar.header("Model Controls")
ticker_input = st.sidebar.text_input("Stock Ticker", value="AAPL").upper().strip()

st.sidebar.subheader("DCF Levers (Tech/Industrials)")
short_term_growth = st.sidebar.slider("Stage 1: High Growth Rate", min_value=-0.10, max_value=0.40, value=0.08, step=0.01)
perpetual_growth = st.sidebar.slider("Stage 3: Terminal Growth", min_value=0.01, max_value=0.04, value=0.025, step=0.0025)

st.sidebar.subheader("DDM Levers (Banks)")
div_growth_rate = st.sidebar.slider("Dividend Growth Rate", min_value=0.01, max_value=0.15, value=0.06, step=0.01)

st.sidebar.subheader("Peer Comps Basket")
custom_peers_input = st.sidebar.text_input(
    "Custom Peers (comma-separated, optional)",
    value="",
    placeholder="e.g. MSFT, GOOG, NVDA, META"
)

run_btn = st.sidebar.button("Run Intrinsic Valuation", type="primary")

if run_btn:
    try:
        with st.spinner(f"Ingesting ledgers and validating {ticker_input}..."):
            info, clean_data = load_and_cache_data(ticker_input)
            model_route = validate_company(info, clean_data)
            macro = load_macro_assumptions()
            current_price = float(info.get('currentPrice') or info.get('regularMarketPrice') or 0.0)

            # Render Live Company Identity Header & Champagne Amber Routing Pill
            company_name = info.get("longName", ticker_input)
            sector = info.get("sector", "Equity Asset")
            exchange = info.get("exchange", "MKT")

            if model_route == "DDM":
                badge_text = "Financial Institution • Dividend Discount Engine (DDM)"
                ddm_result = run_ddm_valuation(
                    info,
                    macro,
                    forecast_years=5,
                    dividend_growth_rate=div_growth_rate,
                    terminal_growth_rate=perpetual_growth
                )
                if ddm_result is None:
                    raise ValueError("DDM valuation did not return a valid result.")
                intrinsic_val, cost_of_capital = ddm_result
            else:
                badge_text = "Standard Corporate • 3-Stage DCF Engine"
                wacc_result = calculate_wacc(info, macro)
                if wacc_result is None:
                    raise ValueError("WACC calculation did not return a valid result.")
                cost_of_capital, mkt_cap, debt = wacc_result
                intrinsic_val = run_dcf_valuation(clean_data, info, macro, cost_of_capital, mkt_cap, debt)

            st.markdown(f"""
                <div style="margin-bottom: 8px;">
                    <span style="font-size: 1.45rem; font-weight: 700; color: #F9FAFB;">{company_name}</span>
                    <span style="color: #9CA3AF; font-size: 0.92rem; margin-left: 10px;">{sector} &bull; {exchange}: {ticker_input}</span>
                </div>
                <div class="model-pill"><span class="status-dot"></span>Active Route: {badge_text}</div>
            """, unsafe_allow_html=True)

            # Persist to Supabase cloud ledger
            log_valuation(ticker_input, model_route, current_price, intrinsic_val, cost_of_capital)

        # --- Top KPIs ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Market Price", f"${current_price:.2f}")
        col2.metric("Intrinsic Value", f"${intrinsic_val:.2f}")
        col3.metric("Discount Rate", f"{cost_of_capital * 100:.2f}%")

        spread = ((intrinsic_val - current_price) / current_price) * 100 if current_price else 0
        verdict = "UNDERVALUED" if intrinsic_val > current_price else "OVERVALUED"
        col4.metric("Spread / Verdict", f"{spread:.1f}%", delta=verdict)

        st.divider()

        # --- Middle Row: Visuals & Sensitivity ---
        mid_col1, mid_col2 = st.columns([1, 1])

        with mid_col1:
            with st.container(border=True):
                st.subheader("Historical Cash Performance")
                plot_df = clean_data.dropna(subset=['Revenue', 'Free Cash Flow'])
                dates = [str(d).split(' ')[0] for d in plot_df.index]

                # --- Background Matplotlib Chart (For PDF Export Only) ---
                fig, ax = plt.subplots(figsize=(6, 3.2))
                x = range(len(dates))
                w = 0.35
                ax.bar([i - w / 2 for i in x], plot_df['Revenue'] / 1e9, w, label="Revenue", color="#4B5563")
                ax.bar([i + w / 2 for i in x], plot_df['Free Cash Flow'] / 1e9, w, label="Free Cash Flow", color="#F59E0B")
                ax.set_ylabel("Billions (USD)")
                ax.set_xticks(list(x))
                ax.set_xticklabels(dates)
                ax.legend()

                # --- Interactive Plotly Chart (For Web UI) ---
                fig_plotly = go.Figure()
                fig_plotly.add_trace(go.Bar(
                    x=dates,
                    y=plot_df['Revenue'] / 1e9,
                    name='Revenue',
                    marker_color='#4B5563'
                ))
                fig_plotly.add_trace(go.Bar(
                    x=dates,
                    y=plot_df['Free Cash Flow'] / 1e9,
                    name='Free Cash Flow',
                    marker_color='#F59E0B'
                ))

                fig_plotly.update_layout(
                    barmode='group',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#9CA3AF', family='Inter'),
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis_title="Billions (USD)"
                )
                st.plotly_chart(fig_plotly, use_container_width=True)

                # --- Multi-Ratio Health Trends ---
                st.subheader("Operating Efficiency & Capital Ratios")
                ratio_tab1, ratio_tab2, ratio_tab3 = st.tabs(["FCF Margin", "Net Margin", "ROIC"])

                with ratio_tab1:
                    fcf_margin = pd.DataFrame({
                        'Date': dates,
                        'FCF Margin (%)': (plot_df['Free Cash Flow'] / plot_df['Revenue']) * 100
                    }).set_index('Date')
                    st.line_chart(fcf_margin, color="#F59E0B", height=190)

                with ratio_tab2:
                    net_margin = pd.DataFrame({
                        'Date': dates,
                        'Net Profit Margin (%)': (plot_df['Net Income'] / plot_df['Revenue']) * 100
                    }).set_index('Date')
                    st.line_chart(net_margin, color="#10B981", height=190)

                with ratio_tab3:
                    if 'Invested Capital' in plot_df.columns and plot_df['Invested Capital'].isna().sum() == 0:
                        tax_rate = macro.get("default_tax_rate", 0.21) if isinstance(macro, dict) else 0.21
                        nopat = plot_df['Operating Income'] * (1 - tax_rate)
                        roic_series = (nopat / plot_df['Invested Capital']) * 100
                        roic_df = pd.DataFrame({'Date': dates, 'ROIC (%)': roic_series}).set_index('Date')
                        st.line_chart(roic_df, color="#9CA3AF", height=190)
                    else:
                        st.caption("Invested capital structure not applicable or missing for this ticker.")

        with mid_col2:
            with st.container(border=True):
                if model_route == "DCF":
                    st.subheader("Valuation Multiverse (Sensitivity)")
                    st.caption("Intrinsic value per share across WACC and terminal growth scenarios")
                    matrix_df = build_sensitivity_matrix(
                        clean_data,
                        info,
                        cost_of_capital,
                        base_g=perpetual_growth,
                        short_term_growth=short_term_growth
                    )
                    st.dataframe(
                        matrix_df.style.highlight_max(axis=None, color='#F59E0B33').format("${:.2f}", na_rep="N/A"),
                        use_container_width=True
                    )
                else:
                    st.subheader("Dividend Policy Analysis")
                    base_div = info.get('dividendRate') or info.get('trailingAnnualDividendRate', 0)
                    payout = (info.get('payoutRatio') or 0) * 100
                    c_div1, c_div2 = st.columns(2)
                    c_div1.metric("Base Dividend (DPS)", f"${base_div:.2f}")
                    c_div2.metric("Payout Ratio", f"{payout:.1f}%")

                    st.subheader("DDM Valuation Multiverse")
                    st.caption("Intrinsic value per share across Cost of Equity and dividend growth scenarios")
                    ddm_matrix = build_ddm_sensitivity_matrix(
                        info,
                        cost_of_capital,
                        div_growth_rate=div_growth_rate,
                        base_terminal_g=perpetual_growth
                    )
                    if not ddm_matrix.empty:
                        st.dataframe(
                            ddm_matrix.style.highlight_max(axis=None, color='#F59E0B33').format("${:.2f}", na_rep="N/A"),
                            use_container_width=True
                        )
                    else:
                        st.caption("Unable to compute sensitivity matrix: Missing or non-positive dividend baseline.")

        st.divider()

        # --- Peer Comparables (Relative Valuation) Engine ---
        st.subheader("Peer Comparables & Relative Valuation")
        custom_peers = tuple(
            [p.strip().upper() for p in custom_peers_input.split(",") if p.strip()]
        ) if custom_peers_input.strip() else ()

        with st.spinner("Benchmarking trading multiples against sector peers..."):
            comps_df, comps_summary = load_cached_comps(ticker_input, info, custom_peers)

        comp_col1, comp_col2 = st.columns([1.25, 1])

        with comp_col1:
            with st.container(border=True):
                st.caption("Trading Multiples Benchmark (Target vs. Sector Peers & Median)")
                st.dataframe(
                    comps_df.style.format({
                        "Price": "${:.2f}",
                        "Trailing P/E": "{:.1f}x",
                        "Forward P/E": "{:.1f}x",
                        "EV/EBITDA": "{:.1f}x",
                        "P/FCF": "{:.1f}x",
                    }, na_rep="N/A"),
                    use_container_width=True,
                    hide_index=True
                )

                implied_rel = comps_summary["implied_relative_price"]
                rel_spread = comps_summary["relative_spread_pct"]
                m_c1, m_c2 = st.columns(2)
                if not pd.isna(implied_rel):
                    rel_verdict = "DISCOUNT TO PEERS" if rel_spread > 0 else "PREMIUM TO PEERS"
                    m_c1.metric("Implied Relative Value", f"${implied_rel:.2f}")
                    m_c2.metric("Relative Spread", f"{rel_spread:+.1f}%", delta=rel_verdict)
                else:
                    st.caption("Insufficient positive peer multiples to compute blended relative value.")

        with comp_col2:
            with st.container(border=True):
                st.caption("Target vs. Peer Median Multiples")
                mult_names = ["Trailing P/E", "Forward P/E", "EV/EBITDA", "P/FCF"]
                target_vals = [comps_summary["target_multiples"].get(m, 0) or 0 for m in mult_names]
                median_vals = [comps_summary["medians"].get(m, 0) or 0 for m in mult_names]

                fig_comps = go.Figure()
                fig_comps.add_trace(go.Bar(
                    x=mult_names,
                    y=target_vals,
                    name=ticker_input,
                    marker_color="#F59E0B"
                ))
                fig_comps.add_trace(go.Bar(
                    x=mult_names,
                    y=median_vals,
                    name="Peer Median",
                    marker_color="#4B5563"
                ))
                fig_comps.update_layout(
                    barmode="group",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#9CA3AF", family="Inter"),
                    margin=dict(l=0, r=0, t=10, b=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    yaxis_title="Multiple (x)",
                    height=310
                )
                st.plotly_chart(fig_comps, use_container_width=True)

        st.divider()

        # --- Bottom Section: Export Tear-Sheet ---
        st.subheader("Institutional Deliverables")
        chart_file = f"{ticker_input}_financials.png"
        fig.savefig(chart_file, dpi=200, bbox_inches='tight')
        plt.close(fig)
        generate_pdf_report(ticker_input, current_price, intrinsic_val, cost_of_capital, chart_file)

        pdf_path = f"{ticker_input}_Valuation_Report.pdf"
        if os.path.exists(pdf_path):
            with open(pdf_path, "rb") as pdf_data:
                st.download_button(
                    label=f"Download {ticker_input} Executive PDF Tear-Sheet",
                    data=pdf_data,
                    file_name=pdf_path,
                    mime="application/pdf"
                )

    except ValuationError as ve:
        st.error(str(ve))
    except Exception as e:
        st.error(f"Execution Error: {e}")