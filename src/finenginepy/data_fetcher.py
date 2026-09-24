import yfinance as yf
import pandas as pd

def fetch_raw_data(ticker_symbol):
    print(f"Opening the ledgers for {ticker_symbol}...")
    stock = yf.Ticker(ticker_symbol)
    
    inc = stock.financials
    bal = stock.balance_sheet
    cf = stock.cashflow
    info = stock.info
    
    return inc, bal, cf, info

def clean_financials(inc, bal, cf):
    print("Extracting core DCF ingredients via Alias Mapping...")
    
    # 1. Alias Dictionaries for Diverse SEC Filings
    rev_aliases = ["Total Revenue", "Operating Revenue", "Revenue"]
    fcf_aliases = ["Free Cash Flow"]
    cf_ops_aliases = ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities", "Total Cash From Operating Activities"]
    capex_aliases = ["Capital Expenditure", "Capital Expenditures", "Payments For Property Plant And Equipment"]
    net_inc_aliases = ["Net Income", "Net Income Common Stockholders", "Net Income From Continuing Operation Net Minority Interest"]
    ebit_aliases = ["Operating Income", "EBIT", "Total Operating Profit/Loss"]
    equity_aliases = ["Stockholders Equity", "Total Stockholder Equity", "Common Stock Equity"]
    debt_aliases = ["Total Debt", "Long Term Debt And Capital Lease Obligation"]
    cash_aliases = ["Cash Cash Equivalents And Short Term Investments", "Cash And Cash Equivalents", "Cash Financial"]

    def extract_row(df, aliases):
        if df is None or df.empty:
            return None
        for alias in aliases:
            if alias in df.index:
                return df.loc[alias]
        return None

    revenue = extract_row(inc, rev_aliases)
    net_income = extract_row(inc, net_inc_aliases)
    ebit = extract_row(inc, ebit_aliases)
    fcf = extract_row(cf, fcf_aliases)
    cf_ops = extract_row(cf, cf_ops_aliases)
    capex = extract_row(cf, capex_aliases)
    
    equity = extract_row(bal, equity_aliases)
    debt = extract_row(bal, debt_aliases)
    cash = extract_row(bal, cash_aliases)

    # Fallback for Free Cash Flow if missing (CapEx is typically reported as negative in cash flow statements)
    if fcf is None and cf_ops is not None and capex is not None:
        fcf = cf_ops - capex.abs()

    # Impute missing line items with 0 if absent
    dates = inc.columns if inc is not None and not inc.empty else cf.columns
    
    clean_dict = {
        "Revenue": revenue if revenue is not None else pd.Series(0, index=dates),
        "Net Income": net_income if net_income is not None else pd.Series(0, index=dates),
        "Operating Income": ebit if ebit is not None else pd.Series(0, index=dates),
        "Free Cash Flow": fcf if fcf is not None else pd.Series(0, index=dates)
    }
    
    clean_df = pd.DataFrame(clean_dict).sort_index()

    # Calculate Invested Capital (Total Debt + Total Equity - Cash)
    if equity is not None and debt is not None:
        bal_dates = bal.columns
        cash_series = cash if cash is not None else pd.Series(0, index=bal_dates)
        invested_cap = (debt + equity - cash_series).sort_index()
        clean_df["Invested Capital"] = invested_cap.reindex(clean_df.index).bfill().ffill()
    else:
        clean_df["Invested Capital"] = None

    return clean_df