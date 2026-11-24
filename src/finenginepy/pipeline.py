from datetime import datetime
from io import BytesIO
import os
import sys

import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def generate_pdf_report(
    ticker: str,
    current_price: float,
    intrinsic_val: float,
    cost_of_capital: float,
    chart_file: str,
) -> str:
    """Generates an executive Private Wealth Gold PDF valuation tear-sheet."""
    print(f"\n[+] Stitching the final PDF Tear-Sheet for {ticker}...")
    pdf_path = f"{ticker}_Valuation_Report.pdf"
    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter

    # Brand Palette
    graphite = colors.HexColor("#16161A")
    amber = colors.HexColor("#F59E0B")
    silver = colors.HexColor("#9CA3AF")
    dark_text = colors.HexColor("#111827")
    card_bg = colors.HexColor("#F9FAFB")
    border_gray = colors.HexColor("#E5E7EB")

    spread_pct = ((intrinsic_val - current_price) / current_price) * 100 if current_price else 0.0
    is_undervalued = intrinsic_val > current_price
    verdict = "UNDERVALUED" if is_undervalued else "OVERVALUED"
    verdict_color = colors.HexColor("#10B981") if is_undervalued else colors.HexColor("#EF4444")

    # 1. Top Executive Graphite Header Banner
    c.setFillColor(graphite)
    c.rect(0, height - 85, width, 85, stroke=0, fill=1)
    c.setStrokeColor(amber)
    c.setLineWidth(3)
    c.line(0, height - 85, width, height - 85)

    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(45, height - 42, "FINENGINE")
    c.setFillColor(amber)
    c.setFont("Helvetica", 18)
    c.drawString(152, height - 42, "|  EXECUTIVE VALUATION TEAR-SHEET")

    c.setFillColor(silver)
    c.setFont("Helvetica", 9)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    c.drawString(45, height - 64, f"Institutional Quantitative Valuation Engine  •  Generated: {timestamp}")

    # 2. Target Asset & Verdict Sub-Header
    c.setFillColor(dark_text)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(45, height - 122, f"Target Equity: {ticker.upper()}")

    # Verdict Pill Badge
    c.setFillColor(verdict_color)
    c.roundRect(width - 175, height - 130, 130, 24, 6, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(width - 110, height - 122, f"{verdict} ({spread_pct:+.1f}%)")

    # 3. Four-Column Monospace KPI Grid
    kpis = [
        ("MARKET PRICE", f"${current_price:.2f}"),
        ("INTRINSIC VALUE", f"${intrinsic_val:.2f}"),
        ("DISCOUNT RATE", f"{cost_of_capital * 100:.2f}%"),
        ("IMPLIED SPREAD", f"{spread_pct:+.1f}%"),
    ]
    box_width = 122
    box_height = 62
    gap = 11
    start_x = 45
    y_pos = height - 210

    for i, (label, val) in enumerate(kpis):
        bx = start_x + i * (box_width + gap)
        c.setFillColor(card_bg)
        c.setStrokeColor(border_gray)
        c.setLineWidth(1)
        c.roundRect(bx, y_pos, box_width, box_height, 6, stroke=1, fill=1)

        # Amber Top Accent Bar on each KPI Card
        c.setStrokeColor(amber)
        c.setLineWidth(2.5)
        c.line(bx + 2, y_pos + box_height, bx + box_width - 2, y_pos + box_height)

        c.setFillColor(colors.HexColor("#6B7280"))
        c.setFont("Helvetica-Bold", 8)
        c.drawString(bx + 12, y_pos + 40, label)

        c.setFillColor(dark_text)
        c.setFont("Courier-Bold", 14)
        c.drawString(bx + 12, y_pos + 16, val)

    # 4. Historical Cash Performance Chart Section
    c.setFillColor(dark_text)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(45, height - 250, "Historical Revenue & Free Cash Flow Trajectory")
    c.setStrokeColor(border_gray)
    c.setLineWidth(1)
    c.line(45, height - 258, width - 45, height - 258)

    if os.path.exists(chart_file):
        c.drawImage(
            chart_file,
            45,
            height - 545,
            width=width - 90,
            height=265,
            preserveAspectRatio=True,
            anchor="c",
        )

    # 5. Institutional Methodology & Footer Disclosure
    c.setStrokeColor(amber)
    c.setLineWidth(1.5)
    c.line(45, 78, width - 45, 78)

    c.setFillColor(colors.HexColor("#4B5563"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(45, 62, "METHODOLOGY & GOVERNANCE DISCLOSURE")
    c.setFont("Helvetica", 7.5)
    c.drawString(
        45,
        48,
        "Intrinsic valuation computed via automated 3-Stage Discounted Cash Flow (DCF) or Dividend Discount Model (DDM) routing.",
    )
    c.drawString(
        45,
        36,
        "For institutional research and informational purposes only. Does not constitute investment advice or a solicitation to trade.",
    )

    c.save()
    print(f"[+] Tear-Sheet generated successfully: {pdf_path}")
    return pdf_path


def generate_excel_workbook(
    ticker: str,
    model_route: str,
    current_price: float,
    intrinsic_val: float,
    cost_of_capital: float,
    sensitivity_df: pd.DataFrame,
    comps_df: pd.DataFrame,
    clean_data: pd.DataFrame,
) -> bytes:
    """Builds a 4-sheet institutional Excel model in memory and returns raw bytes."""
    output = BytesIO()
    spread_pct = ((intrinsic_val - current_price) / current_price) * 100 if current_price else 0.0

    summary_df = pd.DataFrame([
        {"Metric": "Ticker", "Value": ticker},
        {"Metric": "Valuation Model", "Value": f"3-Stage {model_route}" if model_route == "DCF" else "Dividend Discount (DDM)"},
        {"Metric": "Market Price ($)", "Value": round(current_price, 2)},
        {"Metric": "Intrinsic Value ($)", "Value": round(intrinsic_val, 2)},
        {"Metric": "Discount Rate (%)", "Value": round(cost_of_capital * 100, 2)},
        {"Metric": "Intrinsic Spread (%)", "Value": round(spread_pct, 2)},
    ])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="Executive Summary", index=False)
        if sensitivity_df is not None and not sensitivity_df.empty:
            sensitivity_df.to_excel(writer, sheet_name="Sensitivity Matrix")
        if comps_df is not None and not comps_df.empty:
            comps_df.to_excel(writer, sheet_name="Peer Comparables", index=False)
        if clean_data is not None and not clean_data.empty:
            clean_data.to_excel(writer, sheet_name="Historical Financials")

    return output.getvalue()


def run_pipeline(ticker_symbol: str):
    from finenginepy.data_fetcher import clean_financials, fetch_raw_data
    from finenginepy.dcf_model import calculate_wacc, load_macro_assumptions, run_dcf_valuation
    from finenginepy.ddm_model import run_ddm_valuation
    from finenginepy.guards import ValuationError, validate_company
    from finenginepy.visuals import plot_financials

    ticker = ticker_symbol.upper().strip()
    print("\n==========================================")
    print(f"      STARTING PIPELINE: {ticker}")
    print("==========================================")

    # 1. Ingestion
    fetched = fetch_raw_data(ticker)
    if fetched is None:
        print(f"\n[x] Could not fetch market data for {ticker}.\n")
        return
    inc, bal, cf, info = fetched
    clean_data = clean_financials(inc, bal, cf)

    # 2. Institutional Guardrail Routing
    try:
        model_route = validate_company(info, clean_data)
    except ValuationError as error:
        print(error)
        print(f"\n[x] Pipeline safely aborted for {ticker}.\n")
        return

    # 3. Valuation Math (Dynamic Execution)
    macro = load_macro_assumptions()

    if model_route == "DDM":
        ddm_res = run_ddm_valuation(info, macro)
        if ddm_res is None:
            print(f"\n[x] DDM calculation failed for {ticker}.\n")
            return
        intrinsic_val, wacc = ddm_res
    else:
        wacc_res = calculate_wacc(info, macro)
        if wacc_res is None:
            print(f"\n[x] WACC calculation failed for {ticker}.\n")
            return
        wacc, mkt_cap, debt = wacc_res
        intrinsic_val = run_dcf_valuation(clean_data, info, macro, wacc, mkt_cap, debt)

    current_price = float(info.get("currentPrice") or info.get("regularMarketPrice") or 0.0)

    # 4. Chart Generation
    plt.close("all")
    plot_financials(clean_data, ticker)
    chart_file = f"{ticker}_financials.png"

    # 5. Report Stitching
    generate_pdf_report(ticker, current_price, intrinsic_val, wacc, chart_file)
    print(f"\n[✓] Finished valuation run for {ticker}.\n")


def main():
    if len(sys.argv) > 1:
        target_ticker = sys.argv[1]
    else:
        target_ticker = input("Enter Stock Ticker (e.g. MSFT, GOOG, NVDA): ")

    run_pipeline(target_ticker)


if __name__ == "__main__":
    main()