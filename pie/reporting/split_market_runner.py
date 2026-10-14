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
    # 09:15 IST = 555 mins, 15:30 IST = 930 mins (plus 15‑min buffer)
    return 555 <= ist_minutes <= 945


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
    """Generate specialized README page: README_INDIA.md or README_US.md with global cross-stock strategy inter-ranking."""
    now = datetime.now(UTC)
    symbols = INDIAN_SYMBOLS if market_type.lower() == "india" else US_SYMBOLS
    target_readme = Path("README_INDIA.md") if market_type.lower() == "india" else Path("README_US.md")
    title = "🇮🇳 Indian Markets (NSE / BSE) Quantitative Multi-Strategy Interleaved Leaderboard" if market_type.lower() == "india" else "🇺🇸 U.S. Markets (NYSE / NASDAQ) Quantitative Multi-Strategy Interleaved Leaderboard"

    # Expand all candidate strategies (Symbol x Strategy) for every symbol
    all_candidate_entries = []
    cash_entries = []

    for sym in symbols:
        file_key = sym.replace("^", "").replace(".NS", "_NS").replace(".BO", "_BO").replace(" ", "_")
        json_file = docs_dir / f"{file_key}.json"
        if json_file.exists():
            try:
                data = json.loads(json_file.read_text(encoding="utf-8"))
                price = data.get("last_price", 0.0)
                regime = data.get("regime_display", "N/A")
                ranked_strats = data.get("ranked_strategies", [])
                cash_setup = data.get("cash_trade_setup")

                # Extract cash swing trade entry if available
                if cash_setup and price > 0:
                    # Look up persistent state tracking for original entry price and start date
                    state_file = Path("state") / f"{sym.replace('^', '').replace('/', '_')}.json"
                    saved_state = {}
                    if state_file.exists():
                        try:
                            saved_state = json.loads(state_file.read_text(encoding="utf-8"))
                        except Exception:
                            pass

                    # Prefer overall trend_score for cash swing trade conviction
                    score_val = float(data.get("trend_score", data.get("fit_score", 0.0))) * 10.0 if float(data.get("trend_score", 0.0)) > 0 else float(data.get("fit_score", 0.0))
                    c_direction = cash_setup.get("direction", "Long / Buy")
                    
                    # If this symbol had an active ongoing trade, preserve original entry
                    orig_entry = saved_state.get("cash_entry")
                    if orig_entry and float(orig_entry) > 0:
                        c_entry = float(orig_entry)
                    else:
                        c_entry = float(cash_setup.get("entry", price))
                        # Persist entry price so subsequent runs track ongoing performance
                        saved_state["cash_entry"] = c_entry
                        saved_state["cash_direction"] = c_direction
                        state_file.write_text(json.dumps(saved_state, indent=2), encoding="utf-8")

                    c_sl = float(cash_setup.get("stop_loss", c_entry * 0.95))
                    c_t1 = float(cash_setup.get("target_1", c_entry * 1.15))
                    c_t2 = float(cash_setup.get("target_2", c_entry * 1.25))
                    c_rr = cash_setup.get("risk_reward", 3.5)
                    
                    # Status logic: Check ongoing performance vs target/SL
                    gain_pct = ((price - c_entry) / c_entry) * 100.0 if "Long" in c_direction else ((c_entry - price) / c_entry) * 100.0
                    
                    if c_direction.startswith("Long") and price >= c_t2:
                        status = f"🎯 Target 2 Reached (+{gain_pct:.1f}%)"
                    elif c_direction.startswith("Long") and price >= c_t1:
                        status = f"✅ Target 1 Reached (+{gain_pct:.1f}% / Trailing SL)"
                    elif c_direction.startswith("Long") and price <= c_sl:
                        status = f"🛑 Stop Loss Hit ({gain_pct:.1f}%)"
                    elif c_direction.startswith("Short") and price <= c_t2:
                        status = f"🎯 Target 2 Reached (+{gain_pct:.1f}%)"
                    elif c_direction.startswith("Short") and price <= c_t1:
                        status = f"✅ Target 1 Reached (+{gain_pct:.1f}% / Trailing SL)"
                    elif c_direction.startswith("Short") and price >= c_sl:
                        status = f"🛑 Stop Loss Hit ({gain_pct:.1f}%)"
                    elif gain_pct > 0:
                        status = f"🟢 Ongoing (+{gain_pct:.1f}%)"
                    else:
                        status = f"🟢 Ongoing ({gain_pct:.1f}%)"

                    cash_entries.append({
                        "symbol": sym,
                        "price": price,
                        "regime": regime,
                        "score": score_val,
                        "direction": c_direction,
                        "entry": c_entry,
                        "stop_loss": c_sl,
                        "target_1": c_t1,
                        "target_2": c_t2,
                        "rr": c_rr,
                        "status": status,
                    })

                if ranked_strats:
                    for strat_item in ranked_strats:
                        score_val = float(strat_item.get("score", 0.0))
                        sdisplay = strat_item.get("strategy_display", "N/A")
                        stype_raw = strat_item.get("strategy_type", "").lower()
                        legs = strat_item.get("legs_summary", "") or data.get("legs_summary", "")

                        # Skip pure cash swing entries from options table
                        if stype_raw in {"cash_swing_long", "cash_swing_short"}:
                            continue

                        if not legs and data.get("estimated_trade") and data["estimated_trade"].get("legs"):
                            raw_legs = " / ".join([l["summary"] for l in data["estimated_trade"]["legs"]])
                            # Apply formatter for both markets to collapse duplicate legs (e.g., butterfly 2x)
                            legs = format_short_indian_strategy(raw_legs)
                        elif legs and market_type.lower() == "india":
                            legs = format_short_indian_strategy(legs.replace("<br>", " / "))
                        elif legs:
                            legs = legs.replace("<br>", " / ")

                        all_candidate_entries.append({
                            "symbol": sym,
                            "price": price,
                            "regime": regime,
                            "score": score_val,
                            "strategy": sdisplay,
                            "legs": legs,
                            "grade": strat_item.get("grade", "N/A"),
                            "rationale": strat_item.get("rationale", "")
                        })
                else:
                    score_val = float(data.get("fit_score", 0.0))
                    sdisplay = data.get("strategy_display", "N/A")
                    legs = ""
                    if data.get("estimated_trade") and data["estimated_trade"].get("legs"):
                        raw_legs = "<br> ".join([l["summary"] for l in data["estimated_trade"]["legs"]])
                        legs = format_short_indian_strategy(raw_legs) if market_type.lower() == "india" else raw_legs.replace("<br>", " / ")

                    all_candidate_entries.append({
                        "symbol": sym,
                        "price": price,
                        "regime": regime,
                        "score": score_val,
                        "strategy": sdisplay,
                        "legs": legs,
                        "grade": "N/A",
                        "rationale": ""
                    })
            except Exception:
                pass

    # Separate indices to always run and display them
    indian_index_set = {"^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS", "^NSEMDCP50", "^BSESN"}
    us_index_set = {"SPY", "QQQ", "IWM", "DIA", "VTI", "VOO"}
    target_index_set = indian_index_set if market_type.lower() == "india" else us_index_set

    index_entries = []
    for entry in all_candidate_entries:
        if entry["symbol"] in target_index_set:
            index_entries.append(entry)

    # Filter out regular equities with score < 70.0 (i.e. Score / 10 < 7.0)
    all_candidate_entries = [e for e in all_candidate_entries if e["score"] >= 70.0]
    cash_entries = [e for e in cash_entries if e["score"] >= 70.0]

    # Sort globally across all candidate strategies (Symbol x Strategy) in descending score order
    all_candidate_entries.sort(key=lambda x: x["score"], reverse=True)
    cash_entries.sort(key=lambda x: x["score"], reverse=True)
    index_entries.sort(key=lambda x: x["score"], reverse=True)

    curr = "₹" if market_type.lower() == "india" else "$"

    content = f"""# {title}

**Last Automated Run**: {format_ist_time(now)}

> **Global Interleaved Ranking**: Evaluated and ordered strictly by quantitative fit score on a **0–10.0 scale** (Minimum Quality Threshold: **Score ≥ 7.0** for individual stocks; Benchmark Indices always tracked).

---

## 🌐 Part 1: Macro Benchmark Indices (Always Tracked & Evaluated)

| Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :--- | :--- | :--- | :---: | :--- | :--- | :---: |
"""
    if not index_entries:
        content += "| *No index data* | - | - | - | - | - | - |\n"
    else:
        seen_index_syms = set()
        for item in index_entries:
            sym = item["symbol"]
            # Show top strategy per index
            if sym in seen_index_syms:
                continue
            seen_index_syms.add(sym)
            price = item["price"]
            regime = item["regime"]
            score_out_of_10 = item["score"] / 10.0
            score_str = f"{score_out_of_10:.1f}"
            strat = item["strategy"]
            leg_str = item["legs"]
            grade = item["grade"]
            content += f"| **{sym}** | {curr}{price:,.2f} | {regime} | **{score_str}** | {strat} | `{leg_str}` | {grade} |\n"

    content += f"""
---

## 📈 Part 2: Cash Market (Equity Swing Calls with Entry, Targets & Stop Loss)

| Rank | Symbol | Price | Regime | Score / 10 | Action | Entry | Stop Loss | Target 1 | Target 2 | R:R | Position Status |
| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
"""

    if not cash_entries:
        content += "| - | *No qualifying setups* | - | - | - | - | - | - | - | - | - | *Score threshold < 7.0* |\n"
    else:
        for idx, item in enumerate(cash_entries[:20], 1):
            score_out_of_10 = item["score"] / 10.0
            score_str = f"{score_out_of_10:.1f}"
            act = "🟢 Buy" if "Long" in item["direction"] else "🔴 Short"
            content += f"| **#{idx}** | **{item['symbol']}** | {curr}{item['price']:,.2f} | {item['regime']} | **{score_str}** | {act} | {curr}{item['entry']:,.2f} | {curr}{item['stop_loss']:,.2f} | {curr}{item['target_1']:,.2f} | {curr}{item['target_2']:,.2f} | {item['rr']}x | {item['status']} |\n"

    content += f"""
---

## ⚡ Part 3: Derivatives Market (Options Spreads, Condors & Futures Leaderboard)

| Rank | Symbol | Price | Market Regime | Score / 10 | Strategy | Structure / Leg Shorthand | Grade |
| :---: | :--- | :--- | :--- | :---: | :--- | :--- | :---: |
"""

    if not all_candidate_entries:
        content += "| - | *No qualifying setups* | - | - | - | - | - | - |\n"
    else:
        for idx, item in enumerate(all_candidate_entries[:30], 1):
            sym = item["symbol"]
            price = item["price"]
            regime = item["regime"]
            score_out_of_10 = item["score"] / 10.0
            score_str = f"{score_out_of_10:.1f}"
            strat = item["strategy"]
            leg_str = item["legs"]
            grade = item["grade"]

            content += f"| **#{idx}** | **{sym}** | {curr}{price:,.2f} | {regime} | **{score_str}** | {strat} | `{leg_str}` | {grade} |\n"

    content += f"""
---

### 🛡️ Execution & Exit Guardrails
- **Cash Swing Exit Rules**: Medium-Term Position (2–6 Months). Target 1 (+15%) triggers partial profit taking & trailing stop loss at EMA20. Target 2 (+25% to 30%) exits full position. Let run as long as trend structure remains intact.
- **Target DTE Window (Derivatives)**: 30–60 DTE Target Expiration Cycle.
- **Take Profit (Derivatives)**: 50% max profit target for Spreads, Ratio Puts & Futures; 25% for Iron Flies & Jade Lizards.
- **21 DTE Review Gate**: Review trade at 21 DTE; close/roll if delta expands past 0.30.
- **14 DTE Mandatory Exit**: Hard exit at 14 DTE to eliminate gamma pin risk.
- **1:1 Stop Loss**: Close position if net loss equals 100% of initial credit collected.
"""

    target_readme.write_text(content, encoding="utf-8")
    print(f"Successfully updated {target_readme} with {len(all_candidate_entries)} unrolled candidate strategies!")



def run_scheduled_pipeline() -> None:
    """Run market data generation based on active market hours or manual trigger."""
    now = datetime.now(UTC)
    in_open = is_indian_market_open(now)
    us_open = is_us_market_open(now)

    print(f"[{format_ist_time(now)}] Checking Market Hours: India Open={in_open}, US Open={us_open}")

    # Generate specialized README pages only for markets that are currently open
    # Indian market: attempt generation even if closed, but log if market is closed.
    if in_open:
        generate_market_readme("india")
    else:
        try:
            print("[WARN] Indian market closed – attempting fallback generation.")
            generate_market_readme("india")
        except Exception as e:
            print(f"[ERROR] Fallback Indian README generation failed: {e}")
    # US market: only generate when open
    if us_open:
        generate_market_readme("us")


if __name__ == "__main__":
    from pie.reporting.generate_web_data import generate_all_web_data
    generate_all_web_data()
    run_scheduled_pipeline()
