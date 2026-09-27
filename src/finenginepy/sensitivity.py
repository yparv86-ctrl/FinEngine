import numpy as np
import pandas as pd

def build_sensitivity_matrix(clean_data, info, base_wacc, base_g=0.025, forecast_years=5, short_term_growth=0.05):
    print("\n[+] Generating Sensitivity Matrix (WACC vs. Terminal Growth)...")
    
    # 1. Define grid ranges
    wacc_range = np.linspace(base_wacc - 0.015, base_wacc + 0.015, 5)
    growth_range = np.linspace(base_g - 0.01, base_g + 0.01, 5)
    
    latest_fcf = clean_data['Free Cash Flow'].dropna().iloc[-1]
    total_cash = info.get("totalCash", 0)
    total_debt = info.get("totalDebt", 0)
    shares = info.get("sharesOutstanding", 1)
    
    # Explicit cash flow projections
    projected_fcf = []
    curr = latest_fcf
    for _ in range(forecast_years):
        curr *= (1 + short_term_growth)
        projected_fcf.append(curr)
        
    matrix = {}

    for g in growth_range:
        col_name = f"g = {g * 100:.2f}%"
        matrix[col_name] = []
        for w in wacc_range:
            if w <= g:
                matrix[col_name].append(np.nan)
                continue
                
            pv_fcf = sum(fcf / ((1 + w) ** i) for i, fcf in enumerate(projected_fcf, start=1))
            tv = (projected_fcf[-1] * (1 + g)) / (w - g)
            pv_tv = tv / ((1 + w) ** forecast_years)
            
            ev = pv_fcf + pv_tv
            equity = ev + total_cash - total_debt
            price = equity / shares
            matrix[col_name].append(round(price, 2))
            
    row_labels = [f"WACC = {w * 100:.2f}%" for w in wacc_range]
    sensitivity_df = pd.DataFrame(matrix, index=row_labels)
    return sensitivity_df


def build_ddm_sensitivity_matrix(info, base_r_e, div_growth_rate=0.06, base_terminal_g=0.025, forecast_years=5):
    print("\n[+] Generating DDM Sensitivity Matrix (Cost of Equity vs. Terminal Dividend Growth)...")
    
    # Baseline dividend per share extraction
    dps = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
    if not dps or dps <= 0:
        payout_ratio = info.get("payoutRatio", 0.30)
        trailing_eps = info.get("trailingEps", 0.0)
        if trailing_eps > 0:
            dps = trailing_eps * payout_ratio
        else:
            return pd.DataFrame()

    r_e_steps = [base_r_e - 0.015, base_r_e - 0.0075, base_r_e, base_r_e + 0.0075, base_r_e + 0.015]
    g_steps = [0.015, 0.020, 0.025, 0.030, 0.035]

    col_names = [f"g = {g * 100:.2f}%" for g in g_steps]
    row_names = [f"r_e = {r * 100:.2f}%" for r in r_e_steps]

    grid_data = []

    for r in r_e_steps:
        row_vals = []
        for g in g_steps:
            if r <= g:
                row_vals.append(None)
                continue
            
            pv_divs = 0.0
            curr_dps = dps
            for yr in range(1, forecast_years + 1):
                curr_dps *= (1 + div_growth_rate)
                pv_divs += curr_dps / ((1 + r) ** yr)

            term_dps = curr_dps * (1 + g)
            term_val = term_dps / (r - g)
            pv_term = term_val / ((1 + r) ** forecast_years)

            intrinsic_val = pv_divs + pv_term
            row_vals.append(round(intrinsic_val, 2))
        grid_data.append(row_vals)

    return pd.DataFrame(grid_data, index=row_names, columns=col_names)


if __name__ == "__main__":
    from finenginepy.data_fetcher import fetch_raw_data, clean_financials
    from finenginepy.dcf_model import load_macro_assumptions, calculate_wacc
    
    inc, bal, cf, info = fetch_raw_data("AAPL")
    clean_data = clean_financials(inc, bal, cf)
    macro = load_macro_assumptions()
    wacc, _, _ = calculate_wacc(info, macro)
    
    grid = build_sensitivity_matrix(clean_data, info, wacc)
    print("\n--- DCF INTRINSIC PRICE MATRIX ($) ---")
    print(grid)

    ddm_grid = build_ddm_sensitivity_matrix(info, base_r_e=0.09)
    print("\n--- DDM INTRINSIC PRICE MATRIX ($) ---")
    print(ddm_grid)