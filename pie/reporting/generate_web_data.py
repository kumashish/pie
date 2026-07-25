"""Generate static JSON market analysis data for GitHub Pages web app deployment."""

import json
from pathlib import Path

from pie.web.server import analyze_symbol

POPULAR_SYMBOLS = [
    # US Benchmarks & Equities
    "SPY",
    "QQQ",
    "AAPL",
    "NVDA",
    "TSLA",
    "MSFT",
    "AMZN",
    # Indian Benchmarks & Equities
    "^NSEI",
    "^NSEBANK",
    "NIFTY_FIN_SERVICE.NS",
    "^NSEMDCP50",
    "^BSESN",
    "TITAN.NS",
    "SUNPHARMA.NS",
    "ICICIBANK.NS",
    "BAJAJ-AUTO.NS",
    "HDFCBANK.NS",
    "HDFCLIFE.NS",
    "HINDALCO.NS",
    "JSWSTEEL.NS",
    "HCLTECH.NS",
    "TCS.NS",
    "SBILIFE.NS",
    "M&M.NS",
    "ULTRACEMCO.NS",
    "BHARTIARTL.NS",
    "BAJAJFINSV.NS",
]


def generate_all_web_data(output_dir: Path = Path("web/data")) -> None:
    """Run market analysis for popular symbols and output JSON files for GitHub Pages."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_index = []

    print(f"Generating static web data for {len(POPULAR_SYMBOLS)} symbols into {output_dir}...")

    for symbol in POPULAR_SYMBOLS:
        try:
            print(f"Analyzing {symbol}...")
            data = analyze_symbol(symbol)
            
            # Save individual symbol JSON file (safe filename)
            safe_name = symbol.replace("^", "").replace(".NS", "_NS").replace(".BO", "_BO").replace(" ", "_")
            file_path = output_dir / f"{safe_name}.json"
            file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

            # Add entry to master index
            summary_index.append({
                "symbol": data["symbol"],
                "file_key": safe_name,
                "last_price": data["last_price"],
                "regime": data["regime"],
                "regime_display": data["regime_display"],
                "fit_score": data["fit_score"],
                "strategy_display": data["strategy_display"],
                "trade_profile": data["trade_profile"],
                "as_of": data["as_of"],
            })
        except Exception as e:
            print(f"⚠️ Warning: Failed to analyze {symbol}: {e}")

    # Write master index file
    index_file = output_dir / "index.json"
    index_file.write_text(json.dumps(summary_index, indent=2), encoding="utf-8")
    print(f"Successfully generated {len(summary_index)} web data files!")


if __name__ == "__main__":
    generate_all_web_data()
