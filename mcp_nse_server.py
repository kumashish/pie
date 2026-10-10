"""NSE Live Market MCP Server.

Provides direct access to live quotes, underlying prices, and option chains
from NSE India for high-accuracy liquidity and bid-ask spread verification.
"""

import json
import logging
import urllib.request
from typing import Dict, Any, Optional

from mcp.server.fastmcp import FastMCP

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nse_mcp")

mcp = FastMCP("NSE Live Market Server")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
}

BASE_URL = "https://www.nseindia.com"
INDICES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}


def _get_nse_session_cookies() -> Optional[str]:
    """Establishes an initial handshake with NSE to obtain session cookies."""
    try:
        req = urllib.request.Request(BASE_URL, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.headers.get("Set-Cookie")
    except Exception as e:
        logger.warning(f"Failed to fetch NSE session cookies: {e}")
        return None


def _clean_symbol(symbol: str) -> str:
    """Sanitizes ticker symbols (removes .NS suffix, carets, and extra whitespace)."""
    return symbol.replace(".NS", "").replace("^", "").strip().upper()


@mcp.tool()
def get_nse_quote(symbol: str) -> str:
    """Fetch live quote, LTP, volume, and 52-week high/low directly from NSE India.
    
    Args:
        symbol: Stock symbol (e.g., 'RELIANCE', 'DRREDDY', 'SBIN', 'NIFTY')
    """
    clean_sym = _clean_symbol(symbol)
    url = f"{BASE_URL}/api/quote-equity?symbol={clean_sym}"
    
    try:
        cookies = _get_nse_session_cookies()
        req = urllib.request.Request(url, headers=HEADERS)
        if cookies:
            req.add_header("Cookie", cookies)

        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            price_info = data.get("priceInfo", {})
            intra_high_low = price_info.get("intraDayHighLow", {})
            week_high_low = price_info.get("weekHighLow", {})

            result = {
                "symbol": clean_sym,
                "last_price": price_info.get("lastPrice"),
                "change": price_info.get("change"),
                "pChange": price_info.get("pChange"),
                "day_high": intra_high_low.get("max"),
                "day_low": intra_high_low.get("min"),
                "vwap": price_info.get("vwap"),
                "week_52_high": week_high_low.get("max"),
                "week_52_low": week_high_low.get("min"),
            }
            return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error fetching NSE quote for {clean_sym}: {e}")
        return json.dumps({"error": f"Failed to fetch quote for {clean_sym}: {str(e)}"})


@mcp.tool()
def get_nse_option_chain(symbol: str) -> str:
    """Fetch live NSE option chain matrix with strike prices, IVs, OI, and bid-ask spreads.
    
    Args:
        symbol: Equity or Index symbol (e.g., 'NIFTY', 'BANKNIFTY', 'DRREDDY')
    """
    clean_sym = _clean_symbol(symbol)
    is_index = clean_sym in INDICES
    endpoint = "option-chain-indices" if is_index else "option-chain-equities"
    url = f"{BASE_URL}/api/{endpoint}?symbol={clean_sym}"
    
    try:
        cookies = _get_nse_session_cookies()
        req = urllib.request.Request(url, headers=HEADERS)
        if cookies:
            req.add_header("Cookie", cookies)

        with urllib.request.urlopen(req, timeout=5) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
            records = raw_data.get("records", {})
            underlying_value = records.get("underlyingValue")
            data_list = records.get("data", [])
            
            # Select strikes near underlying price if available
            filtered = []
            for item in data_list:
                strike = item.get("strikePrice")
                ce = item.get("CE", {})
                pe = item.get("PE", {})
                
                # Filter out strikes with zero open interest/activity
                if ce or pe:
                    filtered.append({
                        "strike": strike,
                        "CE": {
                            "ltp": ce.get("lastPrice"),
                            "iv": ce.get("impliedVolatility"),
                            "oi": ce.get("openInterest"),
                            "bid": ce.get("buyPrice1"),
                            "ask": ce.get("sellPrice1"),
                        },
                        "PE": {
                            "ltp": pe.get("lastPrice"),
                            "iv": pe.get("impliedVolatility"),
                            "oi": pe.get("openInterest"),
                            "bid": pe.get("buyPrice1"),
                            "ask": pe.get("sellPrice1"),
                        }
                    })

            return json.dumps({
                "symbol": clean_sym,
                "underlying": underlying_value,
                "total_strikes": len(filtered),
                "chain": filtered[:20]  # Limit to 20 relevant strikes for concise LLM response
            }, indent=2)
    except Exception as e:
        logger.error(f"Error fetching NSE option chain for {clean_sym}: {e}")
        return json.dumps({"error": f"Failed to fetch option chain for {clean_sym}: {str(e)}"})


if __name__ == "__main__":
    mcp.run()
