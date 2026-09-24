import yaml
import pandas as pd

def load_macro_assumptions():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)["macro"]

def calculate_wacc(info, macro):
    market_cap = info.get("marketCap", 0)
    total_debt = info.get("totalDebt", 0)
    
    total_capital = market_cap + total_debt
    weight_equity = market_cap / total_capital if total_capital > 0 else 1
    weight_debt = total_debt / total_capital if total_capital > 0 else 0
    
    beta = info.get("beta", 1.0)
    cost_of_equity = macro["risk_free_rate"] + (beta * macro["equity_risk_premium"])
    
    cost_of_debt = 0.05 * (1 - macro["default_tax_rate"])
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt)
    return wacc, market_cap, total_debt

def run_dcf_valuation(clean_data, info, macro, wacc, market_cap, total_debt):
    print("\n[+] Running Dynamic 3-Stage DCF Model...")
    
    # 1. 3-Stage Assumptions
    high_growth_years = 5
    transition_years = 5
    total_forecast_years = high_growth_years + transition_years
    
    # We assign a more aggressive 8% initial growth rate for Stage 1
    high_growth_rate = 0.08 
    perpetual_growth_rate = 0.025
    
    latest_fcf = clean_data['Free Cash Flow'].dropna().iloc[-1]
    
    projected_fcf = []
    current_fcf = latest_fcf
    
    # STAGE 1: High Growth Period (Years 1-5)
    for year in range(1, high_growth_years + 1):
        current_fcf = current_fcf * (1 + high_growth_rate)
        projected_fcf.append(current_fcf)
        
    # STAGE 2: Transition Period (Years 6-10) 
    # Growth rate linearly decays from 8% down to 2.5%
    decay_step = (high_growth_rate - perpetual_growth_rate) / transition_years
    current_growth_rate = high_growth_rate
    
    for year in range(1, transition_years + 1):
        current_growth_rate -= decay_step
        current_fcf = current_fcf * (1 + current_growth_rate)
        projected_fcf.append(current_fcf)
        
    # 3. Discount all 10 explicit years to Present Value (PV)
    pv_of_fcf = 0
    for year, fcf in enumerate(projected_fcf, start=1):
        discount_factor = (1 + wacc) ** year
        pv_of_fcf += fcf / discount_factor
        
    # STAGE 3: Terminal Value (Stable Growth to Infinity)
    terminal_value = (projected_fcf[-1] * (1 + perpetual_growth_rate)) / (wacc - perpetual_growth_rate)
    pv_of_terminal_value = terminal_value / ((1 + wacc) ** total_forecast_years)
    
    # Calculate Final Equity Value
    enterprise_value = pv_of_fcf + pv_of_terminal_value
    total_cash = info.get("totalCash", 0)
    equity_value = enterprise_value + total_cash - total_debt
    
    shares_outstanding = info.get("sharesOutstanding", 1)
    intrinsic_value_per_share = equity_value / shares_outstanding
    
    print(f"10-Year Explicit PV: ${pv_of_fcf / 1e9:.2f} Billion")
    print(f"Terminal Value PV: ${pv_of_terminal_value / 1e9:.2f} Billion")
    print(f"Enterprise Value: ${enterprise_value / 1e9:.2f} Billion")
    print(f"Equity Value: ${equity_value / 1e9:.2f} Billion")
    
    return intrinsic_value_per_share

if __name__ == "__main__":
    from finenginepy.data_fetcher import fetch_raw_data, clean_financials
    inc, bal, cf, info = fetch_raw_data("AAPL")
    clean_data = clean_financials(inc, bal, cf)
    macro = load_macro_assumptions()
    wacc, mkt_cap, debt = calculate_wacc(info, macro)
    run_dcf_valuation(clean_data, info, macro, wacc, mkt_cap, debt)