class ValuationError(Exception):
    """Custom exception raised when a company cannot be reliably valued with a DCF."""
    pass

def validate_company(info, clean_data):
    print("\n[+] Inspecting company profile and guardrails...")
    
    sector = info.get("sector", "Unknown")
    industry = info.get("industry", "Unknown")
    
    # 1. Financial Sector Guardrail
    forbidden_sectors = ["Financial Services", "Financial"]
    forbidden_industries = ["Banks—Diversified", "Banks—Regional", "Insurance—Life", "Insurance—Diversified"]
    
    if sector in forbidden_sectors or any(ind in industry for ind in forbidden_industries):
        raise ValuationError(
            f"\n[!] VALUATION HALTED: {info.get('shortName', 'This company')} is in the {sector} sector ({industry}).\n"
            f"    DCF models cannot value financial institutions because debt functions as operational inventory.\n"
            f"    Recommendation: Use an Equity / Dividend Discount Model (DDM) instead."
        )
        
    # 2. Historical Cash Flow Guardrail
    valid_fcf = clean_data['Free Cash Flow'].dropna()
    if valid_fcf.empty:
        raise ValuationError("\n[!] VALUATION HALTED: No historical Free Cash Flow records could be extracted.")
        
    latest_fcf = valid_fcf.iloc[-1]
    if latest_fcf <= 0:
        print(f"[-] WARNING: Latest Free Cash Flow is negative (${latest_fcf / 1e6:.2f}M).")
        print("    Intrinsic valuation on early-stage or distressed cash flows may produce negative equity value.")

    print(f"[✓] Guardrails passed: Sector is '{sector}' ({industry}). Proceeding to math engine.")