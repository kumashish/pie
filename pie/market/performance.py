"""Historical Signal Performance Analytics and Win-Rate Tracker."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class PerformanceSummary:
    """Quantitative performance analytics summary."""

    total_signals: int
    active_signals: int
    closed_signals: int
    winning_trades: int
    losing_trades: int
    win_rate_percent: Optional[float]
    avg_return_percent: Optional[float]
    cumulative_return_percent: Optional[float]
    max_drawdown_percent: Optional[float]

    def format_markdown_table(self) -> str:
        """Format metrics as a Markdown analytics table."""
        if self.closed_signals == 0 or self.win_rate_percent is None:
            win_rate_str = "N/A"
            avg_ret_str = "N/A"
            cum_ret_str = "N/A"
            dd_str = "N/A"
        else:
            win_rate_str = f"**{self.win_rate_percent:.1f}%**"
            avg_ret_str = f"+{self.avg_return_percent:.1f}%" if self.avg_return_percent >= 0 else f"{self.avg_return_percent:.1f}%"
            cum_ret_str = f"**+{self.cumulative_return_percent:.1f}%**" if self.cumulative_return_percent >= 0 else f"**{self.cumulative_return_percent:.1f}%**"
            dd_str = f"{self.max_drawdown_percent:.1f}%"

        lines = [
            "### 📈 Signal Performance & Win-Rate Analytics",
            "| Total Signals | Active Signals | Closed Trades | Win Rate | Avg Return | Cumulative Return | Max Drawdown |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
            f"| {self.total_signals} | {self.active_signals} | {self.closed_signals} | {win_rate_str} | {avg_ret_str} | {cum_ret_str} | {dd_str} |",
        ]
        return "\n".join(lines)


class PerformanceTracker:
    """Calculates historical performance metrics from signal state and backtests."""

    def __init__(
        self,
        snapshot_path: Path = Path("reports/market/snapshot.json"),
        history_path: Path = Path("state/closed_trades.json"),
    ):
        self.snapshot_path = snapshot_path
        self.history_path = history_path

    def calculate_summary(self, extra_trades: Optional[list[dict]] = None) -> PerformanceSummary:
        """Compute 100% empirical performance analytics from snapshots and closed trade history."""
        active_count = 0
        closed_count = 0
        returns: list[float] = []

        if self.snapshot_path.exists():
            try:
                data = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
                for row in data:
                    signal = row.get("signal", "")
                    ret = row.get("realized_return_pct")
                    if "exit" in signal.lower() or "close" in signal.lower():
                        closed_count += 1
                        if ret is not None:
                            returns.append(float(ret))
                    else:
                        active_count += 1
            except Exception:
                pass

        if self.history_path.exists():
            try:
                history_data = json.loads(self.history_path.read_text(encoding="utf-8"))
                for trade in history_data:
                    closed_count += 1
                    if "return_pct" in trade:
                        returns.append(float(trade["return_pct"]))
            except Exception:
                pass

        if extra_trades:
            for trade in extra_trades:
                closed_count += 1
                if "return_pct" in trade:
                    returns.append(float(trade["return_pct"]))

        total_signals = active_count + closed_count
        wins = sum(1 for r in returns if r > 0)
        losses = sum(1 for r in returns if r <= 0)

        if returns:
            win_rate = (wins / len(returns)) * 100.0
            avg_ret = sum(returns) / len(returns)
            cum_ret = sum(returns)
            max_dd = min(returns) if min(returns) < 0 else 0.0
        else:
            win_rate = None
            avg_ret = None
            cum_ret = None
            max_dd = None

        return PerformanceSummary(
            total_signals=total_signals,
            active_signals=active_count,
            closed_signals=closed_count,
            winning_trades=wins,
            losing_trades=losses,
            win_rate_percent=win_rate,
            avg_return_percent=avg_ret,
            cumulative_return_percent=cum_ret,
            max_drawdown_percent=max_dd,
        )
