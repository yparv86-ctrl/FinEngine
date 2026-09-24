import yaml
import pandas as pd

def load_macro_assumptions():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)["macro"]

def calculate_cost_of_equity(info, macro):
    beta = info.get("beta", 1.0)
    risk_free_rate = macro["risk_free_rate"]
    equity_risk_premium = macro["equity_risk_premium"]
    
    # Capital Asset Pricing Model (CAPM)
    cost_of_equity = risk_free_rate + (beta * equity_risk_premium)
    return cost_of_equity

def run_ddm_valuation(info, macro, forecast_years=5, dividend_growth_rate=0.06, terminal_growth_rate=0.025):
    print("\n[+] Running Dividend Discount Model (DDM)...")
    
    cost_of_equity = calculate_cost_of_equity(info, macro)
    
    # Extract baseline dividend per share
    dps = info.get("dividendRate") or info.get("trailingAnnualDividendRate")
    
    if not dps or dps <= 0:
        # Fallback: Estimate DPS from net income and payout ratio if direct rate is missing
        payout_ratio = info.get("payoutRatio", 0.30)
        trailing_eps = info.get("trailingEps", 0.0)
        if trailing_eps > 0:
            dps = trailing_eps * payout_ratio
        else:
            raise ValueError("Company has zero or negative dividend payments. DDM cannot produce a valuation.")
            
    print(f"Base Dividend Per Share (DPS_0): ${dps:.2f}")
    print(f"Cost of Equity (r_e): {cost_of_equity * 100:.2f}%")
    
    # 1. Project Explicit Dividends
    projected_dividends = []
    current_dps = dps
    for year in range(1, forecast_years + 1):
        current_dps *= (1 + dividend_growth_rate)
        projected_dividends.append(current_dps)
        
    # 2. Discount Dividends to Present Value
    pv_dividends = 0.0
    for year, dividend in enumerate(projected_dividends, start=1):
        pv_dividends += dividend / ((1 + cost_of_equity) ** year)
        
    # 3. Terminal Value via Gordon Growth
    terminal_dps = projected_dividends[-1] * (1 + terminal_growth_rate)
    
    if cost_of_equity <= terminal_growth_rate:
        raise ValueError("Cost of Equity must be strictly greater than terminal dividend growth rate.")
        
    terminal_value = terminal_dps / (cost_of_equity - terminal_growth_rate)
    pv_terminal_value = terminal_value / ((1 + cost_of_equity) ** forecast_years)
    
    intrinsic_value_per_share = pv_dividends + pv_terminal_value
    
    print(f"PV of {forecast_years}-Year Dividends: ${pv_dividends:.2f}")
    print(f"PV of Terminal Value: ${pv_terminal_value:.2f}")
    print(f"Intrinsic Value per Share: ${intrinsic_value_per_share:.2f}")
    
    return intrinsic_value_per_share, cost_of_equity