"""Split market data generation & README updates into Indian vs US Market files.

Execution Timing Schedule:
- Indian Markets (NSE/BSE): Run during Indian Market hours (9:15 AM - 3:30 PM IST / 03:45 UTC - 10:00 UTC).
- US Markets (NYSE/NASDAQ): Run during US Market hours (9:30 AM - 4:00 PM EST / 13:30 UTC - 20:00 UTC).
"""

import json
from datetime import UTC, datetime
from pathlib import Path

from pie.web.server import analyze_symbol
from pie.reporting.readme_update import format_ist_time, get_strategy_display_name, format_fit_score_badge, calculate_since, format_short_indian_strategy

INDIAN_SYMBOLS = [
    "^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS", "^NSEMDCP50", "^BSESN",
    "RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS",
    "BHARTIARTL.NS", "ITC.NS", "SBIN.NS", "LT.NS", "BAJFINANCE.NS",
    "HINDUNILVR.NS", "MARUTI.NS", "TATAMOTORS.NS", "AXISBANK.NS", "KOTAKBANK.NS",
    "SUNPHARMA.NS", "TITAN.NS", "ULTRACEMCO.NS", "JSWSTEEL.NS", "HINDALCO.NS",
    "SBILIFE.NS", "HDFCLIFE.NS", "BAJAJ-AUTO.NS", "BAJAJFINSV.NS", "M&M.NS",
    "HCLTECH.NS", "WIPRO.NS", "ADANIENT.NS", "ADANIPORTS.NS", "NTPC.NS",
    "POWERGRID.NS", "COALINDIA.NS", "ONGC.NS", "BPCL.NS", "GRASIM.NS",
    "NESTLEIND.NS", "CIPLA.NS", "DRREDDY.NS", "APOLLOHOSP.NS", "EICHERMOT.NS",
    "DIVISLAB.NS", "HEROMOTOCO.NS", "TATASTEEL.NS", "TECHM.NS", "BRITANNIA.NS",
    "BEL.NS", "TRENT.NS", "SHRIRAMFIN.NS"
]

US_SYMBOLS = [
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO", "XLF", "XLE", "XLK", "SOXX",
    "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "META", "TSLA", "AMD", "NFLX", "PLTR",
    "INTC", "COIN", "MSTR", "MARA", "RIOT", "AVGO", "ARM", "SMCI", "SOXL", "QCOM",
    "MU", "AMAT", "ORCL", "IBM", "UVXY", "JPM", "BAC", "WFC", "GS", "MS",
    "V", "MA", "WMT", "COST", "TGT", "DIS", "NKE", "UNH", "LLY", "XOM"
]

ALL_SYMBOLS = US_SYMBOLS + INDIAN_SYMBOLS


def is_indian_market_open(now_utc: datetime | None = None) -> bool:
    """Check if Indian NSE/BSE markets are currently open (09:15 to 15:30 IST / Mon-Fri)."""
    if now_utc is None:
        now_utc = datetime.now(UTC)
    # Mon=0, Sun=6
    if now_utc.weekday() >= 5:
        return False
    # IST = UTC + 5:30
    ist_minutes = now_utc.hour * 60 + now_utc.minute + 330
    # 09:15 IST = 555 mins, 15:30 IST = 930 mins
    return 555 <= ist_minutes <= 930


def is_us_market_open(now_utc: datetime | None = None) -> bool:
    """Check if US NYSE/NASDAQ markets are currently open (09:30 to 16:00 EST / 13:30 to 20:00 UTC / Mon-Fri)."""
    if now_utc is None:
        now_utc = datetime.now(UTC)
    if now_utc.weekday() >= 5:
        return False
    utc_minutes = now_utc.hour * 60 + now_utc.minute
    # 13:30 UTC = 810 mins, 20:00 UTC = 1200 mins
    return 810 <= utc_minutes <= 1200


def generate_market_readme(market_type: str = "india", docs_dir: Path = Path("docs/data")) -> None:
    """Generate specialized README page: README_INDIA.md or README_US.md."""
    now = datetime.now(UTC)
    symbols = INDIAN_SYMBOLS if market_type.lower() == "india" else US_SYMBOLS
    target_readme = Path("README_INDIA.md") if market_type.lower() == "india" else Path("README_US.md")
    title = "🇮🇳 Indian Markets (NSE / BSE) Quantitative Trade Dashboard" if market_type.lower() == "india" else "🇺🇸 U.S. Markets (NYSE / NASDAQ) Quantitative Trade Dashboard"

    rows = []
    for sym in symbols:
        file_key = sym.replace("^", "").replace(".NS", "_NS").replace(".BO", "_BO").replace(" ", "_")
        json_file = docs_dir / f"{file_key}.json"
        if json_file.exists():
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                rows.append(data)
            except Exception:
                pass

    # Sort by fit_score descending
    rows.sort(key=lambda x: x.get("fit_score", 0.0), reverse=True)

    content = f"""# {title}

**Last Automated Run**: {format_ist_time(now)}

---

### 🏆 Top Quantitative {('Indian' if market_type.lower() == 'india' else 'U.S.')} Trade Recommendations

| Symbol | Price | Market Regime | Score | Strategy | Structure / Leg Shorthand |
| :--- | :--- | :--- | :---: | :--- | :--- |
"""

    for item in rows[:25]:
        sym = item.get("symbol", "")
        price = item.get("last_price", 0.0)
        curr = "₹" if market_type.lower() == "india" else "$"
        regime = item.get("regime_display", "N/A")
        score = item.get("fit_score", 0.0)
        strat = item.get("strategy_display", "N/A")

        leg_str = ""
        if item.get("estimated_trade") and item["estimated_trade"].get("legs"):
            raw = "<br> ".join([l["summary"] for l in item["estimated_trade"]["legs"]])
            leg_str = format_short_indian_strategy(raw) if market_type.lower() == "india" else raw.replace("<br>", " / ")

        content += f"| **{sym}** | {curr}{price:,.2f} | {regime} | **{score/10.0:.1f}/10** | {strat} | `{leg_str}` |\n"

    content += f"""
---

### 🛡️ Execution & Exit Guardrails
- **Target DTE Window**: 30–60 DTE Target Expiration Cycle.
- **Take Profit**: 50% max profit target for Spreads & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
"""

    target_readme.write_text(content, encoding="utf-8")
    print(f"Successfully updated {target_readme}!")


def run_scheduled_pipeline() -> None:
    """Run market data generation based on active market hours or manual trigger."""
    now = datetime.now(UTC)
    in_open = is_indian_market_open(now)
    us_open = is_us_market_open(now)

    print(f"[{format_ist_time(now)}] Checking Market Hours: India Open={in_open}, US Open={us_open}")

    # Generate specialized README pages for both markets
    generate_market_readme("india")
    generate_market_readme("us")


if __name__ == "__main__":
    from pie.reporting.generate_web_data import generate_all_web_data
    generate_all_web_data()
    run_scheduled_pipeline()
