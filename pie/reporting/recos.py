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

def update_root_readme(docs_dir: Path = Path("docs/data"), readme_path: Path = Path("README.md")) -> None:
    """Synchronize root README.md snapshot and reports/market/snapshot.json from all docs/data JSONs."""
    from pie.reporting.readme_update import load_market_data_from_json, update_readme_snapshot
    snapshot_list = []
    for f in docs_dir.glob("*.json"):
        if f.name == "index.json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            sym = data.get("symbol")
            if not sym:
                continue
            ranked = data.get("ranked_strategies", [])
            top = ranked[0] if ranked else None
            top_score = float(top["score"]) if top else float(data.get("fit_score", 0.0))
            top_stype = top.get("strategy_type", data.get("strategy_type", "")) if top else data.get("strategy_type", "")
            top_display = top.get("strategy_display", data.get("strategy_display", "")) if top else data.get("strategy_display", "")
            top_legs = top.get("legs_summary", "") if top else ""
            if not top_legs and data.get("estimated_trade") and data["estimated_trade"].get("legs"):
                top_legs = " / ".join([l["summary"] for l in data["estimated_trade"]["legs"]])

            as_of = data.get("as_of")
            regime = data.get("regime", "neutral")
            regime_display = data.get("regime_display", "Neutral")

            snapshot_list.append({
                "symbol": sym,
                "market": sym,
                "last_updated": as_of if as_of else datetime.now(UTC).isoformat(),
                "trend": f"🟢 {regime_display}" if "bull" in regime.lower() else (f"🔴 {regime_display}" if "bear" in regime.lower() else f"🟡 {regime_display}"),
                "strategy": top_legs or top_display,
                "strategy_type": top_stype,
                "fit_score": top_score,
                "signal": "Active" if top_score >= 80.0 else "New",
                "signal_since": as_of if as_of else datetime.now(UTC).isoformat(),
            })
        except Exception:
            pass

    if snapshot_list and readme_path.exists():
        try:
            snapshot_path = Path("reports/market/snapshot.json")
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot_path.write_text(json.dumps(snapshot_list, indent=2), encoding="utf-8")
            market_rows = load_market_data_from_json(snapshot_path)
            update_readme_snapshot(readme_path, market_rows)
            print(f"[recos] Successfully synchronized root README.md with {len(snapshot_list)} market snapshots!")
        except Exception as e:
            print(f"[recos] [Warning] Failed to update root README.md: {e}")

def main() -> None:
    now = datetime.now(UTC)
    # Always refresh all market benchmark indices on every run
    refresh_indices()

    # Determine which market to generate
    market_arg = sys.argv[1].lower() if len(sys.argv) > 1 else None

    if market_arg in ("india", "us"):
        print(f"[recos] Running recommendations for: {market_arg.upper()}")
        generate_market_readme(market_arg)
    else:
        # Default: refresh both markets so both Indian & US dashboards stay synchronized
        print("[recos] Running recommendations for: INDIA & US")
        generate_market_readme("india")
        generate_market_readme("us")

    # Update root README.md snapshot as well
    update_root_readme()
    print("[recos] Done.")

if __name__ == "__main__":
    main()
