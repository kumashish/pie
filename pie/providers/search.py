"""Company Name to Ticker Symbol Resolution & Autocomplete Search Provider."""

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass

COMPANY_NAME_MAP = {
    "nifty": "^NSEI",
    "nifty 50": "^NSEI",
    "nifty50": "^NSEI",
    "bank nifty": "^NSEBANK",
    "banknifty": "^NSEBANK",
    "fin nifty": "NIFTY_FIN_SERVICE.NS",
    "finnifty": "NIFTY_FIN_SERVICE.NS",
    "midcap nifty": "^NSEMDCP50",
    "midcapnifty": "^NSEMDCP50",
    "sensex": "^BSESN",
    "bse sensex": "^BSESN",
    "titan": "TITAN.NS",
    "titan company": "TITAN.NS",
    "reliance": "RELIANCE.NS",
    "reliance industries": "RELIANCE.NS",
    "tcs": "TCS.NS",
    "tata consultancy": "TCS.NS",
    "tata motors": "TATAMOTORS.NS",
    "tata steel": "TATASTEEL.NS",
    "infosys": "INFY.NS",
    "infy": "INFY.NS",
    "hdfc": "HDFCBANK.NS",
    "hdfc bank": "HDFCBANK.NS",
    "icici": "ICICIBANK.NS",
    "icici bank": "ICICIBANK.NS",
    "state bank": "SBIN.NS",
    "sbi": "SBIN.NS",
    "bajaj auto": "BAJAJ-AUTO.NS",
    "sun pharma": "SUNPHARMA.NS",
    "hindalco": "HINDALCO.NS",
    "hdfc life": "HDFCLIFE.NS",
    "apple": "AAPL",
    "nvidia": "NVDA",
    "microsoft": "MSFT",
    "tesla": "TSLA",
    "amazon": "AMZN",
    "google": "GOOGL",
    "alphabet": "GOOGL",
    "meta": "META",
    "facebook": "META",
    "spy": "SPY",
    "qqq": "QQQ",
}


@dataclass(frozen=True, slots=True)
class SearchResult:
    symbol: str
    name: str
    exch_disp: str


class TickerSearchProvider:
    """Resolves company names and partial inputs to valid market tickers."""

    @staticmethod
    def resolve_ticker(query: str) -> str:
        """Resolve a search string (company name or ticker) to a canonical symbol."""
        q_clean = query.strip().lower()
        if q_clean in COMPANY_NAME_MAP:
            return COMPANY_NAME_MAP[q_clean]

        # Check partial matching in dictionary
        for name, sym in COMPANY_NAME_MAP.items():
            if q_clean == name or name.startswith(q_clean):
                return sym

        # Query Yahoo Finance search API for dynamic resolution
        results = TickerSearchProvider.search_tickers(query)
        if results:
            return results[0].symbol

        return query.strip().upper()

    @staticmethod
    def search_tickers(query: str) -> tuple[SearchResult, ...]:
        """Search company names and symbols via Yahoo Finance API with local fallback."""
        if not query or len(query.strip()) < 2:
            return ()

        q_clean = query.strip().lower()
        matched = []

        # Local match first
        for name, sym in COMPANY_NAME_MAP.items():
            if q_clean in name or q_clean in sym.lower():
                matched.append(SearchResult(symbol=sym, name=name.title(), exch_disp="US/NSE"))

        # Remote query Yahoo Finance search API
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query.strip())}&quotesCount=5"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            )
            with urllib.request.urlopen(req, timeout=4) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            for quote in data.get("quotes", []):
                sym = quote.get("symbol")
                short_name = quote.get("shortname", quote.get("longname", sym))
                exch = quote.get("exchDisp", "Market")
                if sym and not any(m.symbol == sym for m in matched):
                    matched.append(SearchResult(symbol=sym, name=short_name, exch_disp=exch))
        except Exception:
            pass

        return tuple(matched[:6])
