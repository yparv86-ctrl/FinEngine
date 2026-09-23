import pandas as pd
from data_fetcher import fetch_raw_data, clean_financials
from dcf_model import load_macro_assumptions, calculate_wacc, run_dcf_valuation
from guards import validate_company, ValuationError

def run_screener(tickers):
    print(f"\n[+] Initializing Screener for {len(tickers)} assets...")
    macro = load_macro_assumptions()
    results = []

    for ticker in tickers:
        print(f"\n--- Scanning {ticker} ---")
        try:
            # 1. Fetch & Clean
            inc, bal, cf, info = fetch_raw_data(ticker)
            clean_data = clean_financials(inc, bal, cf)
            
            # 2. Guardrails (Will skip banks automatically)
            validate_company(info, clean_data)
            
            # 3. Valuation
            wacc, mkt_cap, debt = calculate_wacc(info, macro)
            intrinsic_val = run_dcf_valuation(clean_data, info, macro, wacc, mkt_cap, debt)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            
            # Calculate how far off the market is from our model
            if current_price > 0:
                spread = ((intrinsic_val - current_price) / current_price) * 100
            else:
                spread = 0
                
            results.append({
                "Ticker": ticker,
                "Market Price": f"${current_price:.2f}",
                "Intrinsic Value": f"${intrinsic_val:.2f}",
                "Spread": f"{spread:.2f}%",
                "Verdict": "Undervalued" if intrinsic_val > current_price else "Overvalued"
            })
            
        except ValuationError as error:
            # Caught by guards.py
            print(f"[!] Skipped {ticker}: Failed Guardrails.")
            results.append({
                "Ticker": ticker,
                "Market Price": "-",
                "Intrinsic Value": "-",
                "Spread": "-",
                "Verdict": "Skipped (Invalid Structure)"
            })
        except Exception as error:
            # Caught by unforeseen API crashes
            print(f"[x] Error scanning {ticker}: {error}")
            results.append({
                "Ticker": ticker,
                "Market Price": "-",
                "Intrinsic Value": "-",
                "Spread": "-",
                "Verdict": "Error (Data Missing)"
            })

    # Convert the results dictionary into a Pandas DataFrame and print it as a clean Markdown table
    df = pd.DataFrame(results)
    print("\n================ FINAL SCREENER RESULTS ================\n")
    print(df.to_markdown(index=False))

if __name__ == "__main__":
    # A mix of standard tech, a bank (JPM), and an industrial stock (CAT)
    target_list = ["AAPL", "GOOG", "JPM", "MSFT", "CAT"]
    run_screener(target_list)