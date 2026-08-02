"""Generate static JSON market analysis data for GitHub Pages web app deployment."""

import json
from pathlib import Path

from pie.web.server import analyze_symbol

POPULAR_SYMBOLS = [
    # Top 50 Most Heavily Traded US Stocks & ETFs
    # ETFs & Benchmarks (10)
    "SPY",
    "QQQ",
    "IWM",
    "DIA",
    "VTI",
    "VOO",
    "XLF",
    "XLE",
    "XLK",
    "SOXX",
    # Tech, AI & Mega-Caps (20)
    "NVDA",
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AMD",
    "NFLX",
    "PLTR",
    "INTC",
    "COIN",
    "AVGO",
    "ARM",
    "SMCI",
    "QCOM",
    "MU",
    "AMAT",
    "ORCL",
    "IBM",
    # Financials, Retail, Industrial & Healthcare (20)
    "JPM",
    "BAC",
    "WFC",
    "GS",
    "MS",
    "V",
    "MA",
    "WMT",
    "COST",
    "TGT",
    "DIS",
    "NKE",
    "UNH",
    "LLY",
    "JNJ",
    "PFE",
    "XOM",
    "CVX",
    "CAT",
    "GE",
    # Indian Benchmark Indices (5)
    "^NSEI",
    "^NSEBANK",
    "NIFTY_FIN_SERVICE.NS",
    "^NSEMDCP50",
    "^BSESN",
    # NIFTY 50 & Top Indian Blue-Chips
    "RELIANCE.NS",
    "TCS.NS",
    "HDFCBANK.NS",
    "ICICIBANK.NS",
    "INFY.NS",
    "BHARTIARTL.NS",
    "ITC.NS",
    "SBIN.NS",
    "LT.NS",
    "BAJFINANCE.NS",
    "HINDUNILVR.NS",
    "MARUTI.NS",
    "TATAMOTORS.NS",
    "AXISBANK.NS",
    "KOTAKBANK.NS",
    "SUNPHARMA.NS",
    "TITAN.NS",
    "ULTRACEMCO.NS",
    "JSWSTEEL.NS",
    "HINDALCO.NS",
    "SBILIFE.NS",
    "HDFCLIFE.NS",
    "BAJAJ-AUTO.NS",
    "BAJAJFINSV.NS",
    "M&M.NS",
    "HCLTECH.NS",
    "WIPRO.NS",
    "ADANIENT.NS",
    "ADANIPORTS.NS",
    "NTPC.NS",
    "POWERGRID.NS",
    "COALINDIA.NS",
    "ONGC.NS",
    "BPCL.NS",
    "GRASIM.NS",
    "NESTLEIND.NS",
    "CIPLA.NS",
    "DRREDDY.NS",
    "APOLLOHOSP.NS",
    "EICHERMOT.NS",
    "DIVISLAB.NS",
    "HEROMOTOCO.NS",
    "TATASTEEL.NS",
    "TECHM.NS",
    "BRITANNIA.NS",
    "BEL.NS",
    "TRENT.NS",
    "SHRIRAMFIN.NS",
]


def generate_all_web_data(output_dir: Path = Path("web/data"), docs_dir: Path = Path("docs/data")) -> None:
    """Run market analysis for popular symbols and output JSON files for GitHub Pages."""
    output_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    summary_index = []

    print(f"Generating static web data for {len(POPULAR_SYMBOLS)} symbols into {output_dir} and {docs_dir}...")

    for symbol in POPULAR_SYMBOLS:
        try:
            print(f"Analyzing {symbol}...")
            data = analyze_symbol(symbol)
            
            # Save individual symbol JSON file (safe filename)
            safe_name = symbol.replace("^", "").replace(".NS", "_NS").replace(".BO", "_BO").replace(" ", "_")
            content = json.dumps(data, indent=2)
            (output_dir / f"{safe_name}.json").write_text(content, encoding="utf-8")
            (docs_dir / f"{safe_name}.json").write_text(content, encoding="utf-8")

            # Add entry to master index
            # Determine if this signal is a high‑score (fit_score >= 8)
            is_high = data.get("fit_score", 0) >= 8
            summary_index.append({
                "symbol": data["symbol"],
                "file_key": safe_name,
                "last_price": data["last_price"],
                "regime": data["regime"],
                "regime_display": data["regime_display"],
                "fit_score": data["fit_score"],
                "strategy_display": data["strategy_display"],
                "trade_profile": data["trade_profile"],
                "trade_category": data.get("trade_category", "options"),
                "cash_trade_setup": data.get("cash_trade_setup"),
                "as_of": data["as_of"],
                "is_high_score": is_high,
            })
            # Update persistent high‑score list
            if is_high:
                import os
                high_path = os.path.join(os.path.dirname(__file__), "high_score_signals.json")
                try:
                    with open(high_path, "r", encoding="utf-8") as f:
                        high_list = json.load(f)
                except FileNotFoundError:
                    high_list = []
                # Avoid duplicates by symbol
                if not any(item["symbol"] == data["symbol"] for item in high_list):
                    high_list.append({
                        "symbol": data["symbol"],
                        "fit_score": data["fit_score"],
                        "first_seen": data["as_of"],
                        "status": "open",
                    })
                    with open(high_path, "w", encoding="utf-8") as f:
                        json.dump(high_list, f, indent=2)
        except Exception as e:
            print(f"[Warning] Failed to analyze {symbol}: {e}")

    # Write master index file
    index_content = json.dumps(summary_index, indent=2)
    (output_dir / "index.json").write_text(index_content, encoding="utf-8")
    (docs_dir / "index.json").write_text(index_content, encoding="utf-8")
    print(f"Successfully generated {len(summary_index)} web data files!")


if __name__ == "__main__":
    generate_all_web_data()
