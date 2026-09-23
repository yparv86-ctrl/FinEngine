import yfinance as yf
import pandas as pd

def fetch_raw_data(ticker_symbol):
    print(f"Opening the ledgers for {ticker_symbol}...")
    ticker = yf.Ticker(ticker_symbol)
    
    # Flip columns to read oldest -> newest (left to right)
    income_stmt = ticker.financials.iloc[:, ::-1]
    balance_sheet = ticker.balance_sheet.iloc[:, ::-1]
    cash_flow = ticker.cashflow.iloc[:, ::-1]
    
    return income_stmt, balance_sheet, cash_flow, ticker.info

def clean_financials(income, balance, cashflow):
    print("Extracting core DCF ingredients via Alias Mapping...")
    clean_df = pd.DataFrame()
    
    # The Rosetta Stone: Map our target metrics to all known yfinance API variations
    aliases = {
        'Revenue': ['Total Revenue', 'Operating Revenue', 'Revenue'],
        'Operating CF': ['Operating Cash Flow', 'Total Cash From Operating Activities', 'Net Cash From Operating Activities'],
        'CapEx': ['Capital Expenditure', 'Capital Expenditures', 'Property Plant And Equipment', 'Purchases Of Property Plant And Equipment']
    }
    
    # Helper function to scan the ledger for any matching alias
    def extract_row(df, possible_names):
        for name in possible_names:
            if name in df.index:
                return df.loc[name]
        return None # Return None only if absolutely no variations match
        
    clean_df['Revenue'] = extract_row(income, aliases['Revenue'])
    clean_df['Operating CF'] = extract_row(cashflow, aliases['Operating CF'])
    
    capex_row = extract_row(cashflow, aliases['CapEx'])
    if capex_row is not None:
        clean_df['CapEx'] = capex_row.abs()
    else:
        # GIGO Fallback: We fill with 0 so the math engine doesn't crash, but warn the user loudly
        print("\n[-] WARNING: CapEx line item completely missing from API. Imputing as 0.")
        clean_df['CapEx'] = 0
        
    clean_df['Free Cash Flow'] = clean_df['Operating CF'] - clean_df['CapEx']
    return clean_df