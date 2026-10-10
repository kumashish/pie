import json
import urllib.request
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("NSE Live Market Server")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


@mcp.tool()
def get_nse_quote(symbol: str) -> str:
    """Fetch live quote, LTP, volume, and 52-week high/low directly from NSE India.
    
    Args:
        symbol: Stock symbol without .NS suffix (e.g. 'RELIANCE', 'DRREDDY', 'SBIN', 'NIFTY')
    """
    clean_sym = symbol.replace(".NS", "").replace("^", "").strip().upper()
    url = f"https://www.nseindia.com/api/quote-equity?symbol={clean_sym}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        session_req = urllib.request.Request("https://www.nseindia.com", headers=HEADERS)
        with urllib.request.urlopen(session_req, timeout=5) as resp:
            cookies = resp.headers.get("Set-Cookie")
        
        if cookies:
            req.add_header("Cookie", cookies)

        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            price_info = data.get("priceInfo", {})
            return json.dumps({
                "symbol": clean_sym,
                "last_price": price_info.get("lastPrice"),
                "change": price_info.get("change"),
                "pChange": price_info.get("pChange"),
                "day_high": price_info.get("intraDayHighLow", {}).get("max"),
                "day_low": price_info.get("intraDayHighLow", {}).get("min"),
                "vwap": price_info.get("vwap"),
                "week_52_high": price_info.get("weekHighLow", {}).get("max"),
                "week_52_low": price_info.get("weekHighLow", {}).get("min"),
            }, indent=2)
    except Exception as e:
        return f"Error fetching NSE quote for {clean_sym}: {e}"


@mcp.tool()
def get_nse_option_chain(symbol: str) -> str:
    """Fetch live NSE option chain matrix with strike prices, IVs, OI, and bid-ask spreads.
    
    Args:
        symbol: Equity or Index symbol (e.g. 'NIFTY', 'BANKNIFTY', 'DRREDDY')
    """
    clean_sym = symbol.replace(".NS", "").replace("^", "").strip().upper()
    is_index = clean_sym in {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY"}
    endpoint = "option-chain-indices" if is_index else "option-chain-equities"
    url = f"https://www.nseindia.com/api/{endpoint}?symbol={clean_sym}"
    
    try:
        session_req = urllib.request.Request("https://www.nseindia.com", headers=HEADERS)
        with urllib.request.urlopen(session_req, timeout=5) as resp:
            cookies = resp.headers.get("Set-Cookie")
        
        req = urllib.request.Request(url, headers=HEADERS)
        if cookies:
            req.add_header("Cookie", cookies)

        with urllib.request.urlopen(req, timeout=5) as resp:
            raw_data = json.loads(resp.read().decode("utf-8"))
            records = raw_data.get("records", {})
            underlying_value = records.get("underlyingValue")
            data_list = records.get("data", [])
            
            filtered = []
            for item in data_list[:15]:
                filtered.append({
                    "strike": item.get("strikePrice"),
                    "CE_LTP": item.get("CE", {}).get("lastPrice"),
                    "CE_IV": item.get("CE", {}).get("impliedVolatility"),
                    "CE_OI": item.get("CE", {}).get("openInterest"),
                    "PE_LTP": item.get("PE", {}).get("lastPrice"),
                    "PE_IV": item.get("PE", {}).get("impliedVolatility"),
                    "PE_OI": item.get("PE", {}).get("openInterest"),
                })
            
            return json.dumps({"symbol": clean_sym, "underlying": underlying_value, "chain": filtered}, indent=2)
    except Exception as e:
        return f"Error fetching NSE option chain for {clean_sym}: {e}"


if __name__ == "__main__":
    mcp.run()
