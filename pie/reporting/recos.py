#!/usr/bin/env python
"""Recos shortcut command
Runs the market pipeline and outputs only the recommendations (README) for the market that is currently active.
- During Indian market hours (IST) it generates the Indian README.
- Outside Indian hours (i.e., US market hours) it generates the US README.
"""

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

# Import functions from the existing runner
from .split_market_runner import (
    is_indian_market_open,
    is_us_market_open,
    generate_market_readme,
)

def refresh_indices() -> None:
    """Always analyze and refresh market benchmark indices every time."""
    from pie.web.server import analyze_symbol
    index_symbols = [
        # Indian Benchmark Indices
        "^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS", "^NSEMDCP50", "^BSESN",
        # US Benchmark Indices
        "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
    ]
    docs_dir = Path("docs/data")
    web_dir = Path("web/data")
    docs_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)
    print(f"[recos] Always refreshing {len(index_symbols)} market benchmark indices...")
    for sym in index_symbols:
        try:
            data = analyze_symbol(sym)
            safe_name = sym.replace("^", "").replace(".NS", "_NS").replace(".BO", "_BO").replace(" ", "_")
            content = json.dumps(data, indent=2)
            (docs_dir / f"{safe_name}.json").write_text(content, encoding="utf-8")
            (web_dir / f"{safe_name}.json").write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"[recos] [Warning] Failed to refresh index {sym}: {e}")

def main() -> None:
    now = datetime.now(UTC)
    # Always refresh all market benchmark indices on every run
    refresh_indices()

    # Determine which market is open based on the helper functions
    if is_indian_market_open(now):
        market = "india"
    elif is_us_market_open(now):
        market = "us"
    else:
        # Neither market is open – default to Indian for daytime fallback
        market = "india"
    print(f"[recos] Running recommendations for: {market.upper()}")
    generate_market_readme(market)
    print("[recos] Done.")

if __name__ == "__main__":
    main()
