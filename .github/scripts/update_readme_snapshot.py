#!/usr/bin/env python3
"""Update README.md market snapshot table from market_snapshot.json."""

import json
import re
from pathlib import Path


def load_market_data(json_path: str = "market_snapshot.json") -> list[dict]:
    """Load market data from JSON file."""
    try:
        with open(json_path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def format_regime_badge(trend_str: str) -> str:
    """Format market regime with color-coded status badges."""
    clean = trend_str.strip().lower()
    if "strong_bull" in clean or "strong bull" in clean:
        return "🟢 Strong Bull"
    if "bull" in clean:
        return "🟢 Bull"
    if "strong_bear" in clean or "strong bear" in clean:
        return "🔴 Strong Bear"
    if "bear" in clean:
        return "🔴 Bear"
    if "neutral" in clean:
        return "🟡 Neutral"
    return trend_str


def format_fit_score_badge(fit_score: float) -> str:
    """Format strategy fit score as Score / 10."""
    score_out_of_10 = min(10.0, max(0.0, fit_score / 10.0))
    if fit_score > 0.0:
        return f"{score_out_of_10:.1f}/10"
    return "N/A"


def get_strategy_display_name(stype: str) -> str:
    """Get clean color-coded full human-readable strategy name.

    🟢 Bullish Strategies (Call Debit Spread, Naked Put, PMCC)
    🔴 Bearish Strategies (Put Debit Spread, Naked Call)
    🟡 Neutral Strategies (Long Butterfly, Iron Condor, Iron Butterfly, Jade Lizard, etc.)
    """
    clean = stype.lower().replace("_", " ").strip()
    if not clean:
        return "N/A"

    if clean in {"call debit spread", "call_debit_spread"}:
        return "🟢 Call Debit Spread"
    if clean in {"put debit spread", "put_debit_spread"}:
        return "🔴 Put Debit Spread"
    if clean in {"butterfly", "long butterfly", "long_butterfly"}:
        return "🟡 Long Butterfly"
    if clean in {"broken wing butterfly", "broken_wing_butterfly"}:
        return "🟡 Broken Wing Butterfly"
    if clean in {"iron condor", "iron_condor"}:
        return "🟡 Iron Condor"
    if clean in {"iron butterfly", "iron_butterfly"}:
        return "🟡 Iron Butterfly"
    if clean in {"jade lizard", "jade_lizard"}:
        return "🟡 Jade Lizard"
    if clean in {"credit spread", "credit_spread"}:
        return "🟡 Credit Spread"
    if clean in {"naked put", "naked_put"}:
        return "🟢 Naked Put"
    if clean in {"naked call", "naked_call"}:
        return "🔴 Naked Call"
    if clean in {"short strangle", "short_strangle"}:
        return "🟡 Short Strangle"
    if clean in {"collar"}:
        return "🟡 Collar"
    if clean in {"poor mans covered call", "poor_mans_covered_call"}:
        return "🟢 Poor Man's Covered Call"
    return f"🟡 {clean.title()}"


def format_market_table(markets: list[dict]) -> str:
    """Format market snapshot entries into Markdown tables."""
    if not markets:
        return "<!-- MARKET-SNAPSHOT-START -->\n<!-- MARKET-SNAPSHOT-END -->"

    us_benchmarks = {"SPY", "QQQ"}
    indian_benchmarks = {"^NSEI", "^NSEBANK", "NIFTY 50", "BANKNIFTY"}
    simple_debit_types = {"call_debit_spread", "put_debit_spread"}

    table1_us = []
    table2_in = []
    table3_stocks = []
    table4_exits = []

    for market in markets:
        symbol = market.get("symbol", "").upper()
        market_name = market.get("market", "")
        fit_score = float(market.get("fit_score", 0.0))
        stype = market.get("strategy_type", "").lower()
        strategy = market.get("strategy", "")
        signal_raw = market.get("signal", "")

        if strategy == "No Trade":
            continue

        if "exit" in signal_raw.lower() or "close" in signal_raw.lower():
            table4_exits.append(market)
        elif symbol in us_benchmarks or market_name.upper() in us_benchmarks:
            table1_us.append(market)
        elif symbol in indian_benchmarks or market_name.upper() in indian_benchmarks:
            table2_in.append(market)
        else:
            is_simple_debit = stype in simple_debit_types
            if fit_score >= 60.0 and (fit_score > 90.0 or not is_simple_debit):
                table3_stocks.append(market)

    table1_us.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)
    table2_in.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)
    table3_stocks.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)
    table4_exits.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)

    header = "| Market    | Updated   | Regime            | Score     | Strategy          | Signal                 |\n| --------- | --------- | ----------------- | --------- | ----------------- | ---------------------- |"

    lines = ["<!-- MARKET-SNAPSHOT-START -->"]
    lines.append("### 🌐 U.S. Macro Benchmark Indices")
    lines.append(header)
    for market in table1_us:
        market_name = market.get("market", "")
        stype = market.get("strategy_type", "")
        strat_name = get_strategy_display_name(stype)
        fit_badge = format_fit_score_badge(float(market.get("fit_score", 0.0)))
        updated = market.get("updated", "")
        strategy = market.get("strategy", "")
        signal_raw = market.get("signal", "")
        since = market.get("since", "")
        signal_display = "New" if signal_raw.lower() == "new" else f"{signal_raw} ({since})" if since else signal_raw
        lines.append(f"| {market_name:<9} | {updated:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {signal_display:<22} |")

    lines.append("\n### 🌐 Indian Macro Benchmark Indices")
    lines.append(header)
    for market in table2_in:
        market_name = market.get("market", "")
        stype = market.get("strategy_type", "")
        strat_name = get_strategy_display_name(stype)
        fit_badge = format_fit_score_badge(float(market.get("fit_score", 0.0)))
        updated = market.get("updated", "")
        strategy = market.get("strategy", "")
        signal_raw = market.get("signal", "")
        since = market.get("since", "")
        signal_display = "New" if signal_raw.lower() == "new" else f"{signal_raw} ({since})" if since else signal_raw
        lines.append(f"| {market_name:<9} | {updated:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {signal_display:<22} |")

    lines.append("\n### 🎯 High-Conviction (>9/10 Score) & Advanced Range Strategies")
    lines.append(header)
    for market in table3_stocks:
        market_name = market.get("market", "")
        stype = market.get("strategy_type", "")
        strat_name = get_strategy_display_name(stype)
        fit_badge = format_fit_score_badge(float(market.get("fit_score", 0.0)))
        updated = market.get("updated", "")
        strategy = market.get("strategy", "")
        signal_raw = market.get("signal", "")
        since = market.get("since", "")
        signal_display = "New" if signal_raw.lower() == "new" else f"{signal_raw} ({since})" if since else signal_raw
        lines.append(f"| {market_name:<9} | {updated:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {signal_display:<22} |")

    if table4_exits:
        lines.append("\n### ⚡ Recently Closed / Exit Signals (Last 5)")
        lines.append(header)
        for market in table4_exits[:5]:
            market_name = market.get("market", "")
            stype = market.get("strategy_type", "")
            strat_name = get_strategy_display_name(stype)
            fit_badge = format_fit_score_badge(float(market.get("fit_score", 0.0)))
            updated = market.get("updated", "")
            strategy = market.get("strategy", "")
            signal_raw = market.get("signal", "")
            since = market.get("since", "")
            signal_display = f"{signal_raw} ({since})" if since else signal_raw
            lines.append(f"| {market_name:<9} | {updated:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {signal_display:<22} |")
        lines.append('\n<a href="reports/market/closed_trades.md" target="_blank">📜 View Full Closed Trade History ➔</a>\n')

    try:
        from pie.market.performance import PerformanceTracker
        summary = PerformanceTracker().calculate_summary()
        lines.append("\n" + summary.format_markdown_table())
    except Exception:
        pass

    lines.append("<!-- MARKET-SNAPSHOT-END -->")
    return "\n".join(lines)


def update_readme(readme_path: str = "README.md"):
    """Update README.md with new market snapshot."""
    readme = Path(readme_path)
    if not readme.exists():
        print(f"{readme_path} not found")
        return
    
    content = readme.read_text()
    markets = load_market_data()
    new_table = format_market_table(markets)
    
    # Replace content between markers
    pattern = r"<!-- MARKET-SNAPSHOT-START -->.*?<!-- MARKET-SNAPSHOT-END -->"
    updated_content = re.sub(pattern, new_table, content, flags=re.DOTALL)
    
    readme.write_text(updated_content)
    print(f"Updated {readme_path} with {len(markets)} market entries")


if __name__ == "__main__":
    update_readme()
