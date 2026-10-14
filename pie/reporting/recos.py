#!/usr/bin/env python
"""Recos shortcut command
Runs the market pipeline and outputs only the recommendations (README) for the market that is currently active.
- During Indian market hours (IST) it generates the Indian README.
- Outside Indian hours (i.e., US market hours) it generates the US README.
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Import functions from the existing runner
from .split_market_runner import (
    is_indian_market_open,
    is_us_market_open,
    generate_market_readme,
)

def main() -> None:
    now = datetime.now(UTC)
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
