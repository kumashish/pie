"""Plain-text dashboard persistence for individual market-analysis runs."""

import re
from datetime import UTC, datetime
from pathlib import Path

from pie.core.models import MarketSnapshot
from pie.market.indicators.base import IndicatorResult
from pie.market.strategy import StrategyRecommendation
from pie.market.trade_estimate import EstimatedTrade
from pie.market.trend.models import TrendAnalysis


def write_market_report(
    output_dir: Path,
    snapshot: MarketSnapshot,
    indicators: dict[str, IndicatorResult],
    trend: TrendAnalysis,
    recommendation: StrategyRecommendation,
    estimated_trade: EstimatedTrade | None,
) -> Path:
    """Write one timestamped market dashboard and return its path."""
    generated_at = datetime.now(UTC)
    safe_symbol = re.sub(r"[^A-Za-z0-9_-]+", "_", snapshot.symbol).strip("_")
    report_path = output_dir / f"{safe_symbol}_{generated_at:%Y%m%dT%H%M%SZ}.txt"
    indicator_lines = [
        f"{name:<12}: {result.value:,.2f}"
        if result.valid and result.value is not None
        else f"{name:<12}: N/A"
        for name, result in indicators.items()
    ]
    limitation_lines = [f"- {limitation}" for limitation in recommendation.limitations]
    trade_lines = _trade_lines(estimated_trade)
    dashboard = "\n".join(
        [
            "PORTFOLIO INTELLIGENCE ENGINE",
            "=" * 32,
            "",
            f"Generated At : {generated_at:%Y-%m-%d %H:%M:%S UTC}",
            f"Symbol       : {snapshot.symbol}",
            f"Last Price   : {float(snapshot.last_price):,.2f}",
            "",
            "TRADE RECOMMENDATION",
            "=" * 20,
            f"Strategy     : {recommendation.strategy.replace('_', ' ').title()}",
            f"Actionable   : {'✅ Yes' if recommendation.actionable else '❌ No'}",
            "",
            "SUGGESTED TRADE",
            "=" * 15,
            *trade_lines,
            "",
            "Rationale",
            "-" * 9,
            recommendation.rationale,
            *(
                ["", "Limitations", "-" * 11, *limitation_lines]
                if limitation_lines
                else []
            ),
            "",
            "MARKET INTELLIGENCE",
            "-" * 19,
            f"Regime       : {trend.regime.replace('_', ' ').title()}",
            f"Trend Score  : {trend.trend_score.value:.1f} / 10",
            f"Confidence   : {trend.confidence.value:.0%} [Grade: {trend.confidence.grade}]",
            "",
            "INDICATORS",
            "-" * 10,
            *indicator_lines,
            "",
            "TREND EXPLANATION",
            "-" * 17,
            trend.explanation,
        ]
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.write_text(dashboard, encoding="utf-8")
    return report_path


def _trade_lines(estimated_trade: EstimatedTrade | None) -> list[str]:
    if estimated_trade is None:
        return ["No Trade: a live VIX-based estimate is unavailable for this run."]

    leg_lines = [
        f"{leg.action.title()} {leg.right.title():<4}: {leg.strike:,.2f}"
        for leg in estimated_trade.legs
    ]
    exit_lines = [f"- {rule}" for rule in estimated_trade.exit_strategy]
    return [
        f"Expiry       : {estimated_trade.expiration.isoformat()}",
        f"Expected Move: {estimated_trade.expected_move:,.2f}",
        f"VIX          : {estimated_trade.annualized_vix:.2f}",
        f"VIX Source   : {estimated_trade.vix_source}",
        *leg_lines,
        "",
        "Exit Strategy:",
        *exit_lines,
        "",
        estimated_trade.disclaimer,
    ]
