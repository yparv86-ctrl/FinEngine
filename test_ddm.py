import yfinance as yf
from finenginepy.ddm_model import run_ddm_valuation, load_macro_assumptions

print("Fetching JPM data...")
info = yf.Ticker('JPM').info
macro = load_macro_assumptions()

val, r_e = run_ddm_valuation(info, macro)
print(f'\nFinal Calculated JPM Value: ${val:.2f} | Current Price: ${info.get("currentPrice"):.2f}')