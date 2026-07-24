"""Unit tests for notifications dispatcher and performance analytics tracker."""

from pie.market.performance import PerformanceTracker
from pie.reporting.notifications import NotificationDispatcher


def test_notification_dispatcher_formatting():
    dispatcher = NotificationDispatcher()
    sample_row = {
        "symbol": "TITAN.NS",
        "market": "TITAN.NS",
        "fit_score": 9.5,
        "strategy_type": "call_debit_spread",
        "strategy_name": "🟢 Call Debit Spread",
        "strategy": "Buy TITAN 25-Aug-2026-4680-CE<br> Sell TITAN 25-Aug-2026-4870-CE",
        "signal": "Active (Today, 15:47)",
    }

    message = dispatcher.format_signal_message(sample_row)
    assert "PORTFOLIO INTELLIGENCE ALERT" in message
    assert "TITAN.NS" in message
    assert "9.5/10" in message


def test_performance_tracker_summary():
    tracker = PerformanceTracker()
    summary = tracker.calculate_summary()

    assert summary.total_signals >= 50
    assert summary.win_rate_percent >= 0.0
    table_md = summary.format_markdown_table()
    assert "Signal Performance & Win-Rate Analytics" in table_md
    assert "Win Rate" in table_md
