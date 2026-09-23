import yaml
import pandas as pd

def load_macro_assumptions():
    with open("config.yaml", "r") as file:
        return yaml.safe_load(file)["macro"]

def calculate_wacc(info, macro):
    market_cap = info.get("marketCap", 0)
    total_debt = info.get("totalDebt", 0)
    
    total_capital = market_cap + total_debt
    weight_equity = market_cap / total_capital
    weight_debt = total_debt / total_capital
    
    beta = info.get("beta", 1.0)
    cost_of_equity = macro["risk_free_rate"] + (beta * macro["equity_risk_premium"])
    
    cost_of_debt = 0.05 * (1 - macro["default_tax_rate"])
    wacc = (weight_equity * cost_of_equity) + (weight_debt * cost_of_debt)
    return wacc, market_cap, total_debt

def run_dcf_valuation(clean_data, info, macro, wacc, market_cap, total_debt):
    print("\n[+] Running Discounted Cash Flow (DCF) Model...")
    
    # 1. Assumptions for forecasting
    forecast_years = 5
    perpetual_growth_rate = 0.025 # We assume Apple grows at 2.5% forever after year 5 (roughly global GDP growth)
    
    # We grab the most recent Free Cash Flow to start our forecast
    latest_fcf = clean_data['Free Cash Flow'].dropna().iloc[-1]
    
    # We assume a conservative 5% growth rate for the next 5 years
    short_term_growth_rate = 0.05 
    
    # 2. Project Future Cash Flows
    projected_fcf = []
    current_fcf = latest_fcf
    
    for year in range(1, forecast_years + 1):
        current_fcf = current_fcf * (1 + short_term_growth_rate)
        projected_fcf.append(current_fcf)
        
    # 3. Discount the Projected Cash Flows to Present Value (PV)
    pv_of_fcf = 0
    for year, fcf in enumerate(projected_fcf, start=1):
        discount_factor = (1 + wacc) ** year
        pv_of_fcf += fcf / discount_factor
        
    # 4. Calculate Terminal Value (Gordon Growth Model)
    # What is the company worth from year 6 to infinity?
    terminal_value = (projected_fcf[-1] * (1 + perpetual_growth_rate)) / (wacc - perpetual_growth_rate)
    
    # Discount the Terminal Value back to today
    pv_of_terminal_value = terminal_value / ((1 + wacc) ** forecast_years)
    
    # 5. Calculate Enterprise Value and Equity Value
    enterprise_value = pv_of_fcf + pv_of_terminal_value
    
    # Add cash and subtract debt to find the value belonging purely to shareholders
    total_cash = info.get("totalCash", 0)
    equity_value = enterprise_value + total_cash - total_debt
    
    # 6. Calculate Intrinsic Value Per Share
    shares_outstanding = info.get("sharesOutstanding", 1)
    intrinsic_value_per_share = equity_value / shares_outstanding
    
    print(f"Enterprise Value: ${enterprise_value / 1e9:.2f} Billion")
    print(f"Equity Value: ${equity_value / 1e9:.2f} Billion")
    print(f"\n======================================")
    print(f"INTRINSIC VALUE PER SHARE: ${intrinsic_value_per_share:.2f}")
    print(f"CURRENT MARKET PRICE: ${info.get('currentPrice', 0):.2f}")
    print(f"======================================")
    
    return intrinsic_value_per_share

if __name__ == "__main__":
    from data_fetcher import fetch_raw_data, clean_financials
    
    # Run the entire pipeline
    inc, bal, cf, info = fetch_raw_data("AAPL")
    clean_data = clean_financials(inc, bal, cf)
    macro = load_macro_assumptions()
    
    wacc, mkt_cap, debt = calculate_wacc(info, macro)
    run_dcf_valuation(clean_data, info, macro, wacc, mkt_cap, debt)