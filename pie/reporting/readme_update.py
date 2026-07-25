"""Generate market snapshot for README with IST timestamps."""

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TypedDict


class MarketRow(TypedDict):
    """Market snapshot row for README table."""

    symbol: str
    market: str
    updated: str  # "HH:MM IST" or "HH:MM IST (YYYY-MM-DD)"
    trend: str
    strategy: str
    signal: str
    since: str  # "Today, HH:MM" or "Jul 20, HH:MM IST"


def utc_to_ist(dt: datetime | str) -> datetime:
    """Convert UTC datetime or ISO string to IST (UTC+5:30)."""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    ist_offset = timedelta(hours=5, minutes=30)
    return dt.astimezone(UTC).replace(tzinfo=None) + ist_offset


def format_ist_time(dt: datetime | str, include_date: bool = False) -> str:
    """Format datetime or ISO string as IST time string."""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt
    ist_dt = utc_to_ist(dt) if getattr(dt, "tzinfo", None) is not None else dt
    if include_date:
        return ist_dt.strftime("%H:%M IST (%Y-%m-%d)")
    return ist_dt.strftime("%H:%M IST")


def calculate_since(
    signal_date: datetime | str, current_time: datetime | None = None
) -> tuple[str, datetime]:
    """Calculate 'since' duration and format it in hybrid style.

    Args:
        signal_date: when the signal was activated
        current_time: reference time (defaults to now)

    Returns:
        Tuple of (formatted_string, signal_date_in_ist)
        formatted_string examples: "Today, 15:20", "Yesterday, 09:15", "Jul 20, 14:30 IST"
    """
    if current_time is None:
        current_time = datetime.now(UTC)

    signal_ist = utc_to_ist(signal_date)
    current_ist = utc_to_ist(current_time)

    delta_days = (current_ist.date() - signal_ist.date()).days
    time_str = signal_ist.strftime("%H:%M")

    if delta_days == 0:
        return f"Today, {time_str}", signal_ist
    elif delta_days == 1:
        return f"Yesterday, {time_str}", signal_ist
    else:
        # Format as "Mon DD, HH:MM IST" for older dates
        date_str = signal_ist.strftime("%b %d")
        return f"{date_str}, {time_str} IST", signal_ist


def generate_readme_snapshot(
    market_data: list[dict],
    current_time: datetime | None = None,
) -> str:
    """Generate markdown table rows for README.

    Args:
        market_data: list of dicts with keys:
            - symbol: stock symbol (e.g., "^NSEI", "SPY")
            - market: market name (e.g., "NIFTY 50", "SPY")
            - last_updated: datetime of last analysis (UTC)
            - trend: trend emoji and label (e.g., "🟢 Bull")
            - strategy: strategy name
            - signal: signal status (e.g., "NEW", "Active", "Hold")
            - signal_since: datetime when signal started (UTC)
        current_time: reference time for calculations

    Returns:
        Markdown table rows as string
    """
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
def get_trade_profile(stype: str) -> str:
    """Return deterministic strategy profile, target DTE, and short delta target."""
    clean = stype.lower().replace("_", " ").strip()
    if clean in {"covered call", "covered_call"}:
        return "Credit | 30-45 DTE | 20-30 Delta"
    if clean in {"cash secured put", "cash_secured_put", "naked put", "naked_put"}:
        return "Credit | 30-45 DTE | 15-25 Delta"
    if clean in {"credit spread", "credit_spread"}:
        return "Credit | 30-45 DTE | 15-20 Delta"
    if clean in {"iron condor", "iron_condor"}:
        return "Credit | 35-45 DTE | 15 Delta Wings"
    if clean in {"iron butterfly", "iron_butterfly"}:
        return "Credit | 35-45 DTE | ATM Straddle"
    if clean in {"jade lizard", "jade_lizard"}:
        return "Credit | 30-45 DTE | 20 Delta Put"
    if clean in {"naked call", "naked_call"}:
        return "Credit | 30-45 DTE | 15-20 Delta"
    if clean in {"short strangle", "short_strangle"}:
        return "Credit | 30-45 DTE | 15-20 Delta"
    if clean in {"butterfly", "long_butterfly", "broken wing butterfly", "broken_wing_butterfly"}:
        return "Debit | 30-45 DTE | ATM Pin Target"
    if clean in {"call debit spread", "call_debit_spread", "put debit spread", "put_debit_spread"}:
        return "Debit | 30-60 DTE | 50 Delta ITM"
    if clean in {"long call", "long_call", "long put", "long_put"}:
        return "Debit | 60-180 DTE | 60 Delta"
    if clean in {"poor mans covered call", "poor_mans_covered_call"}:
        return "Diagonal | Long 60-90 / Short 20-30 DTE"
    if clean in {"leaps"}:
        return "Debit | 1-2 Yrs | 80 Delta"
    return "Advisory | 30-45 DTE"


def generate_readme_snapshot(
    market_data: list[dict],
    current_time: datetime | None = None,
) -> str:
    """Generate Markdown snapshot tables for README from market data entries."""
    if current_time is None:
        current_time = datetime.now(UTC)

    us_benchmarks = {"SPY", "QQQ"}
    indian_benchmarks = {"^NSEI", "^NSEBANK", "NIFTY 50", "BANKNIFTY"}
    simple_debit_types = {"call_debit_spread", "put_debit_spread"}

    table1_us = []
    table2_in = []
    table3_stocks = []
    table4_exits = []

    for data in market_data:
        symbol = data.get("symbol", "").upper()
        market = data.get("market", "")
        fit_score = float(data.get("fit_score", 0.0))
        stype = data.get("strategy_type", "").lower()
        strategy = data.get("strategy", "")
        signal_raw = data.get("signal", "")

        if strategy == "No Trade":
            continue

        if "exit" in signal_raw.lower() or "close" in signal_raw.lower():
            table4_exits.append(data)
        elif symbol in us_benchmarks or market.upper() in us_benchmarks:
            table1_us.append(data)
        elif symbol in indian_benchmarks or market.upper() in indian_benchmarks:
            table2_in.append(data)
        else:
            is_simple_debit = stype in simple_debit_types
            if fit_score >= 60.0 and (fit_score > 90.0 or not is_simple_debit):
                table3_stocks.append(data)

    # Sort tables strictly by fit_score descending
    table1_us.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)
    table2_in.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)
    table3_stocks.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)
    table4_exits.sort(key=lambda x: float(x.get("fit_score", 0.0)), reverse=True)

    header = "| Market    | Updated   | Regime            | Score     | Strategy          | Trade Profile                      | Signal                 |\n| --------- | --------- | ----------------- | --------- | ----------------- | ---------------------------------- | ---------------------- |"

    output_sections = ["### 🌐 U.S. Macro Benchmark Indices", header]
    for data in table1_us:
        updated_time = format_ist_time(data["last_updated"], include_date=False)
        market = data.get("market", "")
        stype = data.get("strategy_type", "")
        strat_name = get_strategy_display_name(stype)
        fit_badge = format_fit_score_badge(float(data.get("fit_score", 0.0)))
        strategy = data["strategy"]
        signal_raw = data.get("signal", "")
        since_text, _ = calculate_since(data["signal_since"], current_time)
        signal_display = "New" if signal_raw.lower() == "new" else f"{signal_raw} ({since_text})"
        profile_val = get_trade_profile(stype)

        output_sections.append(
            f"| {market:<9} | {updated_time:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {profile_val:<34} | {signal_display:<22} |"
        )

    output_sections.append("\n### 🌐 Indian Macro Benchmark Indices")
    output_sections.append(header)
    for data in table2_in:
        updated_time = format_ist_time(data["last_updated"], include_date=False)
        market = data.get("market", "")
        stype = data.get("strategy_type", "")
        strat_name = get_strategy_display_name(stype)
        fit_badge = format_fit_score_badge(float(data.get("fit_score", 0.0)))
        strategy = data["strategy"]
        signal_raw = data.get("signal", "")
        since_text, _ = calculate_since(data["signal_since"], current_time)
        signal_display = "New" if signal_raw.lower() == "new" else f"{signal_raw} ({since_text})"
        profile_val = get_trade_profile(stype)

        output_sections.append(
            f"| {market:<9} | {updated_time:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {profile_val:<34} | {signal_display:<22} |"
        )

    output_sections.append("\n### 🎯 High-Conviction (>9/10 Score) & Advanced Range Strategies")
    output_sections.append(header)
    for data in table3_stocks:
        updated_time = format_ist_time(data["last_updated"], include_date=False)
        market = data.get("market", "")
        stype = data.get("strategy_type", "")
        strat_name = get_strategy_display_name(stype)
        fit_badge = format_fit_score_badge(float(data.get("fit_score", 0.0)))
        strategy = data["strategy"]
        signal_raw = data.get("signal", "")
        since_text, _ = calculate_since(data["signal_since"], current_time)
        signal_display = "New" if signal_raw.lower() == "new" else f"{signal_raw} ({since_text})"
        profile_val = get_trade_profile(stype)

        output_sections.append(
            f"| {market:<9} | {updated_time:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {profile_val:<34} | {signal_display:<22} |"
        )

    if table4_exits:
        output_sections.append("\n### ⚡ Recently Closed / Exit Signals (Last 5)")
        output_sections.append(header)
        for data in table4_exits[:5]:
            updated_time = format_ist_time(data["last_updated"], include_date=False)
            market = data.get("market", "")
            stype = data.get("strategy_type", "")
            strat_name = get_strategy_display_name(stype)
            fit_badge = format_fit_score_badge(float(data.get("fit_score", 0.0)))
            strategy = data["strategy"]
            signal_raw = data.get("signal", "")
            since_text, _ = calculate_since(data["signal_since"], current_time)
            signal_display = f"{signal_raw} ({since_text})"

            output_sections.append(
                f"| {market:<9} | {updated_time:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {signal_display:<22} |"
            )
        output_sections.append(
            '\n<a href="reports/market/closed_trades.md" target="_blank">📜 View Full Closed Trade History ➔</a>\n'
        )

        # Generate reports/market/closed_trades.md for full history
        try:
            history_file = Path("reports/market/closed_trades.md")
            history_file.parent.mkdir(parents=True, exist_ok=True)
            history_lines = [
                "# 📜 Full Closed Trade History",
                "",
                header,
            ]
            for data in table4_exits:
                updated_time = format_ist_time(data["last_updated"], include_date=False)
                market = data.get("market", "")
                stype = data.get("strategy_type", "")
                strat_name = get_strategy_display_name(stype)
                fit_badge = format_fit_score_badge(float(data.get("fit_score", 0.0)))
                strategy = data["strategy"]
                signal_raw = data.get("signal", "")
                since_text, _ = calculate_since(data["signal_since"], current_time)
                signal_display = f"{signal_raw} ({since_text})"
                history_lines.append(
                    f"| {market:<9} | {updated_time:<9} | {strat_name:<17} | {fit_badge:<9} | {strategy:<17} | {signal_display:<22} |"
                )
            history_file.write_text("\n".join(history_lines), encoding="utf-8")
        except Exception:
            pass

    try:
        from pie.market.performance import PerformanceTracker
        summary = PerformanceTracker().calculate_summary()
        output_sections.append("\n" + summary.format_markdown_table())
    except Exception:
        pass

    return "\n".join(output_sections)


def update_readme_snapshot(
    readme_path: Path,
    market_data: list[dict],
    current_time: datetime | None = None,
) -> bool:
    """Update README.md with new market snapshot table.

    Args:
        readme_path: path to README.md
        market_data: list of market data dicts
        current_time: reference time for calculations

    Returns:
        True if file was modified, False otherwise
    """
    if not readme_path.exists():
        raise FileNotFoundError(f"README not found at {readme_path}")

    readme_content = readme_path.read_text(encoding="utf-8")
    new_table = generate_readme_snapshot(market_data, current_time)

    # Find and replace the snapshot section
    start_marker = "<!-- MARKET-SNAPSHOT-START -->"
    end_marker = "<!-- MARKET-SNAPSHOT-END -->"

    if start_marker not in readme_content or end_marker not in readme_content:
        raise ValueError("README missing MARKET-SNAPSHOT markers")

    start_idx = readme_content.find(start_marker)
    end_idx = readme_content.find(end_marker)

    if start_idx == -1 or end_idx == -1:
        raise ValueError("Could not find snapshot markers in README")

    # Preserve the markers and content before/after
    new_content = (
        readme_content[: start_idx + len(start_marker)]
        + "\n"
        + new_table
        + "\n"
        + readme_content[end_idx:]
    )

    # Check if content actually changed
    if new_content == readme_content:
        return False

    readme_path.write_text(new_content, encoding="utf-8")
    return True


def load_market_data_from_json(json_file: Path) -> list[dict]:
    """Load market data from JSON file.

    JSON format:
    [
        {
            "symbol": "^NSEI",
            "market": "NIFTY 50",
            "last_updated": "2024-01-15T15:20:00Z",
            "trend": "🟢 Bull",
            "strategy": "Call Debit Spread",
            "signal": "NEW",
            "signal_since": "2024-01-15T15:20:00Z"
        },
        ...
    ]
    """
    with open(json_file, encoding="utf-8") as f:
        raw_data = json.load(f)

    # Convert ISO timestamp strings to datetime objects
    for row in raw_data:
        row["last_updated"] = datetime.fromisoformat(row["last_updated"].replace("Z", "+00:00"))
        row["signal_since"] = datetime.fromisoformat(
            row["signal_since"].replace("Z", "+00:00")
        )

    return raw_data


if __name__ == "__main__":
    snapshot_file = Path("reports/market/snapshot.json")
    readme_file = Path("README.md")
    if snapshot_file.exists() and readme_file.exists():
        market_data = load_market_data_from_json(snapshot_file)
        update_readme_snapshot(readme_file, market_data)
