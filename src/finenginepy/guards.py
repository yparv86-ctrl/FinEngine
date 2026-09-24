class ValuationError(Exception):
    """Custom exception raised when a company cannot be reliably valued."""
    pass

def validate_company(info, clean_data):
    print("\n[+] Inspecting company profile and routing...")
    
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
    
    forbidden_sectors = ["Financial Services", "Financial"]
    forbidden_industries = ["Banks—Diversified", "Banks—Regional", "Insurance—Life", "Insurance—Diversified"]
    
    # ROUTE 1: Financial Institutions -> DDM
    if sector in forbidden_sectors or any(ind in industry for ind in forbidden_industries):
        print(f"[*] ROUTER: {sector} detected. Bypassing DCF and routing to Dividend Discount Model (DDM).")
        return "DDM"
        
    # ROUTE 2: Standard Companies -> 3-Stage DCF
    valid_fcf = clean_data['Free Cash Flow'].dropna()
    if valid_fcf.empty:
        raise ValuationError("\n[!] VALUATION HALTED: No historical Free Cash Flow records could be extracted for DCF.")
        
    latest_fcf = valid_fcf.iloc[-1]
    if latest_fcf <= 0:
        print(f"[-] WARNING: Latest Free Cash Flow is negative (${latest_fcf / 1e6:.2f}M).")

    print(f"[✓] ROUTER: Sector is '{sector}'. Routing to 3-Stage DCF.")
    return "DCF"