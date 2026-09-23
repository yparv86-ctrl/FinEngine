import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import matplotlib.pyplot as plt

def generate_pdf_report(ticker, current_price, intrinsic_value, wacc, chart_filename):
    print(f"\n[+] Stitching the final PDF Tear-Sheet for {ticker}...")
    pdf_file = f"{ticker}_Valuation_Report.pdf"
    
    c = canvas.Canvas(pdf_file, pagesize=letter)
    
    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, 730, f"{ticker} - DCF Valuation Tear-Sheet")
    
    # Key Financial Metrics
    c.setFont("Helvetica", 14)
    c.drawString(50, 680, f"Current Market Price: ${current_price:.2f}")
    c.drawString(50, 650, f"Calculated Intrinsic Value: ${intrinsic_value:.2f}")
    c.drawString(50, 620, f"Calculated WACC (Discount Rate): {wacc*100:.2f}%")
    
    # Dynamic Verdict
    c.setFont("Helvetica-Bold", 14)
    if intrinsic_value > current_price:
        verdict = "UNDERVALUED (Potential Buy)"
        c.setFillColorRGB(0, 0.6, 0)
    else:
        verdict = "OVERVALUED (Potential Sell)"
        c.setFillColorRGB(0.8, 0, 0)
        
    c.drawString(50, 580, f"Verdict: {verdict}")
    c.setFillColorRGB(0, 0, 0)
    
    # Embed Chart Asset
    if os.path.exists(chart_filename):
        c.drawString(50, 530, "Historical Overview:")
        c.drawImage(chart_filename, 50, 200, width=500, height=300)
        
    # Academic / Legal Disclaimers
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(50, 100, "DISCLAIMER: For academic and research purposes only. Not investment advice.")
    c.drawString(50, 85, "Relies on external API statements (GIGO). Does not account for qualitative market sentiment.")
    
    c.save()
    print(f"[+] Tear-Sheet generated successfully: {pdf_file}")

def run_pipeline(ticker_symbol):
    from data_fetcher import fetch_raw_data, clean_financials
    from dcf_model import load_macro_assumptions, calculate_wacc, run_dcf_valuation
    from visuals import plot_financials
    from guards import validate_company, ValuationError

    ticker = ticker_symbol.upper().strip()
    print(f"\n==========================================")
    print(f"      STARTING PIPELINE: {ticker}")
    print(f"==========================================")

    # 1. Ingestion
    inc, bal, cf, info = fetch_raw_data(ticker)
    clean_data = clean_financials(inc, bal, cf)
    
    # 2. Institutional Guardrail Verification
    try:
        validate_company(info, clean_data)
    except ValuationError as error:
        print(error)
        print(f"\n[x] Pipeline safely aborted for {ticker}.\n")
        return
    
    # 3. Valuation Math
    macro = load_macro_assumptions()
    wacc, mkt_cap, debt = calculate_wacc(info, macro)
    intrinsic_val = run_dcf_valuation(clean_data, info, macro, wacc, mkt_cap, debt)
    current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
    
    # 4. Chart Generation (Save without blocking popups)
    plt.close('all')  # Prevent window blocking
    plot_financials(clean_data, ticker)
    chart_file = f"{ticker}_financials.png"
    
    # 5. Report Stitching
    generate_pdf_report(ticker, current_price, intrinsic_val, wacc, chart_file)
    print(f"\n[✓] Finished valuation run for {ticker}.\n")

if __name__ == "__main__":
    # Check if a ticker was passed in the terminal command
    if len(sys.argv) > 1:
        target_ticker = sys.argv[1]
    else:
        # Prompt the user directly if they ran the script without arguments
        target_ticker = input("Enter Stock Ticker (e.g. MSFT, GOOG, NVDA): ")
        
    run_pipeline(target_ticker)