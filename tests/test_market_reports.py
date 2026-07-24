from datetime import datetime
from decimal import Decimal
from pathlib import Path

from pie.core.models import MarketSnapshot
from pie.market.indicators.base import IndicatorResult
from pie.market.strategy import StrategyRecommendation, StrategyType
from pie.market.trend.models import ConfidenceScore, MarketRegime, TrendAnalysis, TrendScore
from pie.reporting.market import write_market_report
from pie.reporting.readme_update import generate_readme_snapshot


def test_write_market_report_creates_timestamped_dashboard(tmp_path: Path) -> None:
    snapshot = MarketSnapshot(
        symbol="^NSEI",
        observed_at=datetime(2026, 1, 1),
        last_price=Decimal("24000"),
        volume=0,
    )
    trend = TrendAnalysis(
        symbol="^NSEI",
        timestamp=datetime(2026, 1, 1),
        trend_score=TrendScore(value=7.5),
        confidence=ConfidenceScore(value=1.0),
        regime=MarketRegime.BULL,
        explanation="Test explanation",
        indicator_values={"EMA20": 23900.0},
    )

    report_path = write_market_report(
        tmp_path,
        snapshot,
        {"EMA20": IndicatorResult("EMA20", 23900.0, True, True)},
        trend,
        StrategyRecommendation(
            strategy=StrategyType.CALL_DEBIT_SPREAD,
            actionable=True,
            rationale="Test recommendation",
        ),
        None,
    )

    dashboard = report_path.read_text(encoding="utf-8")

    assert report_path.name.startswith("NSEI_")
    assert report_path.suffix == ".txt"
    assert "PORTFOLIO INTELLIGENCE ENGINE" in dashboard
    assert "Strategy     : Call Debit Spread" in dashboard
    assert "No Trade: a live VIX-based estimate is unavailable" in dashboard


def test_generate_readme_snapshot_filters_strong_trends_and_always_includes_core_indices() -> None:
    now = datetime(2026, 7, 24, 12, 0, 0)
    market_data = [
        {
            "symbol": "^NSEI",
            "market": "NIFTY 50",
            "last_updated": datetime(2026, 7, 24, 12, 0, 0),
            "trend": "🔴 Bear",
            "fit_score": 73.9,
            "strategy": "Put Spread",
            "signal": "Active",
            "signal_since": datetime(2026, 7, 24, 12, 0, 0),
        },
        {
            "symbol": "AAPL",
            "market": "AAPL",
            "last_updated": datetime(2026, 7, 24, 12, 0, 0),
            "trend": "🟡 Neutral",
            "fit_score": 0.0,
            "strategy": "No Trade",
            "signal": "Hold",
            "signal_since": datetime(2026, 7, 24, 12, 0, 0),
        },
        {
            "symbol": "INFY.NS",
            "market": "INFY.NS",
            "last_updated": datetime(2026, 7, 24, 12, 0, 0),
            "trend": "🔴 Strong Bear",
            "fit_score": 85.0,
            "strategy": "Put Spread",
            "signal": "Active",
            "signal_since": datetime(2026, 7, 24, 12, 0, 0),
        },
    ]

    snapshot_md = generate_readme_snapshot(market_data, current_time=now)
    assert "NIFTY 50" in snapshot_md
    assert "INFY.NS" in snapshot_md
    assert "AAPL" not in snapshot_md

