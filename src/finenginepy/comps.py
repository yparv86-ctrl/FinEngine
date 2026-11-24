import numpy as np
import pandas as pd
import yfinance as yf

# Curated institutional peer baskets by sector and key industries
SECTOR_PEERS = {
    "Technology": ["AAPL", "MSFT", "GOOG", "NVDA", "META", "ORCL"],
    "Financial Services": ["JPM", "BAC", "WFC", "C", "GS", "MS"],
    "Consumer Cyclical": ["AMZN", "TSLA", "HD", "MCD", "NKE"],
    "Consumer Defensive": ["PG", "KO", "PEP", "WMT", "COST"],
    "Healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK"],
    "Industrials": ["CAT", "GE", "HON", "UNP", "DE"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
    "Communication Services": ["GOOG", "META", "NFLX", "DIS", "TMUS"],
    "Utilities": ["NEE", "DUK", "SO", "AEP", "SRE"],
    "Real Estate": ["PLD", "AMT", "EQIX", "SPG", "O"],
    "Basic Materials": ["LIN", "SHW", "FCX", "NEM", "APD"],
}


def get_default_peers(ticker: str, sector: str, max_peers: int = 4) -> list[str]:
    """Returns a default list of sector peers excluding the target ticker."""
    ticker = ticker.upper().strip()
    candidates = SECTOR_PEERS.get(sector, ["AAPL", "MSFT", "GOOG", "AMZN", "JPM"])
    peers = [p for p in candidates if p != ticker]
    return peers[:max_peers]


def _extract_multiples(ticker: str, preloaded_info: dict | None = None) -> dict:
    """Extracts and sanitizes P/E, Forward P/E, EV/EBITDA, and P/FCF for a single ticker."""
    info = preloaded_info if preloaded_info is not None else yf.Ticker(ticker).info

    price = info.get("currentPrice") or info.get("regularMarketPrice") or np.nan
    mkt_cap = info.get("marketCap")
    fcf = info.get("freeCashflow")

    trailing_pe = info.get("trailingPE")
    forward_pe = info.get("forwardPE")
    ev_ebitda = info.get("enterpriseToEbitda")

    # Calculate P/FCF = Market Cap / Free Cash Flow (only meaningful when FCF > 0)
    if mkt_cap and fcf and fcf > 0:
        p_fcf = mkt_cap / fcf
    else:
        p_fcf = np.nan

    def _clean_multiple(val):
        if val is None or not isinstance(val, (int, float)) or np.isnan(val):
            return np.nan
        # Filter out negative or extreme outlier multiples (> 250x)
        return float(val) if 0 < val < 250 else np.nan

    return {
        "Ticker": ticker.upper(),
        "Company": info.get("shortName") or ticker.upper(),
        "Price": float(price) if price and not np.isnan(price) else np.nan,
        "Trailing P/E": _clean_multiple(trailing_pe),
        "Forward P/E": _clean_multiple(forward_pe),
        "EV/EBITDA": _clean_multiple(ev_ebitda),
        "P/FCF": _clean_multiple(p_fcf),
    }


def run_peer_comps(
    target_ticker: str,
    target_info: dict,
    peer_tickers: list[str] | None = None
) -> tuple[pd.DataFrame, dict]:
    """
    Builds a Peer Comparables DataFrame (Target + Peers + Peer Median row)
    and calculates an implied relative valuation for the target ticker.
    """
    target_ticker = target_ticker.upper().strip()
    sector = target_info.get("sector", "Technology")

    if not peer_tickers:
        peer_tickers = get_default_peers(target_ticker, sector)
    else:
        peer_tickers = [p.upper().strip() for p in peer_tickers if p.strip() and p.upper().strip() != target_ticker]

    target_row = _extract_multiples(target_ticker, preloaded_info=target_info)
    peer_rows = []
    for peer in peer_tickers:
        try:
            peer_rows.append(_extract_multiples(peer))
        except Exception:
            continue

    peers_df = pd.DataFrame(peer_rows)
    multiple_cols = ["Trailing P/E", "Forward P/E", "EV/EBITDA", "P/FCF"]

    # Compute Peer Medians
    if not peers_df.empty:
        medians = {col: peers_df[col].median(skipna=True) for col in multiple_cols}
    else:
        medians = {col: np.nan for col in multiple_cols}

    median_row = {
        "Ticker": "PEER MEDIAN",
        "Company": f"{sector} Benchmark",
        "Price": np.nan,
        **medians,
    }

    full_df = pd.DataFrame([target_row] + peer_rows + [median_row])

    # Calculate Implied Share Price across available relative multiples
    target_price = target_row["Price"]
    implied_prices = []
    for col in multiple_cols:
        t_mult = target_row.get(col, np.nan)
        m_mult = medians.get(col, np.nan)
        if not np.isnan(t_mult) and not np.isnan(m_mult) and t_mult > 0 and not np.isnan(target_price):
            implied_prices.append(target_price * (m_mult / t_mult))

    blended_implied_price = float(np.mean(implied_prices)) if implied_prices else np.nan
    rel_spread_pct = (
        ((blended_implied_price - target_price) / target_price) * 100
        if not np.isnan(blended_implied_price) and target_price > 0
        else np.nan
    )

    summary = {
        "peer_tickers": peer_tickers,
        "medians": medians,
        "target_multiples": {col: target_row[col] for col in multiple_cols},
        "implied_relative_price": blended_implied_price,
        "relative_spread_pct": rel_spread_pct,
    }

    return full_df, summary