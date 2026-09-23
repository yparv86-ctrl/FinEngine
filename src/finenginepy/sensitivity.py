import numpy as np
import pandas as pd

def build_sensitivity_matrix(clean_data, info, base_wacc, base_g=0.025, forecast_years=5, short_term_growth=0.05):
    print("\n[+] Generating Sensitivity Matrix (WACC vs. Terminal Growth)...")
    
    # 1. Define the grid ranges
    wacc_range = np.linspace(base_wacc - 0.015, base_wacc + 0.015, 5) # 5 steps around base WACC
    growth_range = np.linspace(base_g - 0.01, base_g + 0.01, 5)        # 5 steps around base terminal growth
    
    latest_fcf = clean_data['Free Cash Flow'].dropna().iloc[-1]
    total_cash = info.get("totalCash", 0)
    total_debt = info.get("totalDebt", 0)
    shares = info.get("sharesOutstanding", 1)
    
    # Pre-calculate projected cash flows
    projected_fcf = []
    curr = latest_fcf
    for _ in range(forecast_years):
        curr *= (1 + short_term_growth)
        projected_fcf.append(curr)
        
    matrix = {}

    for g in growth_range:
        col_name = f"g = {g*100:.2f}%"
        matrix[col_name] = []
        for w in wacc_range:
            if w <= g:
                # Math breaks if discount rate is lower than growth rate
                matrix[col_name].append(np.nan)
                continue
                
            # Present value of explicit forecast
            pv_fcf = sum(fcf / ((1 + w) ** i) for i, fcf in enumerate(projected_fcf, start=1))
            
            # Terminal value discounted to present
            tv = (projected_fcf[-1] * (1 + g)) / (w - g)
            pv_tv = tv / ((1 + w) ** forecast_years)
            
            # Intrinsic share price
            ev = pv_fcf + pv_tv
            equity = ev + total_cash - total_debt
            price = equity / shares
            matrix[col_name].append(round(price, 2))
            
    row_labels = [f"WACC = {w*100:.2f}%" for w in wacc_range]
    sensitivity_df = pd.DataFrame(matrix, index=row_labels)
    return sensitivity_df

if __name__ == "__main__":
    from data_fetcher import fetch_raw_data, clean_financials
    from dcf_model import load_macro_assumptions, calculate_wacc
    
    inc, bal, cf, info = fetch_raw_data("AAPL")
    clean_data = clean_financials(inc, bal, cf)
    macro = load_macro_assumptions()
    wacc, _, _ = calculate_wacc(info, macro)
    
    grid = build_sensitivity_matrix(clean_data, info, wacc)
    print("\n--- INTRINSIC PRICE MATRIX ($) ---")
    print(grid)