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
    playbook_res = None
    if snapshot.symbol.upper() in {"^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS"} or snapshot.symbol.upper().startswith("^NSE"):
        from pie.market.nifty_income import evaluate_nifty_mean_reversion
        try:
            playbook_res = evaluate_nifty_mean_reversion(
                symbol=snapshot.symbol,
                last_price=float(snapshot.last_price),
                indicators=indicators,
            )
        except Exception:
            playbook_res = None

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
            *(
                [
                    "",
                    "NIFTY INCOME PLAYBOOK v1.4 (MEAN REVERSION)",
                    "-" * 43,
                    f"Status       : {playbook_res.status.value}",
                    f"Close vs 200 : {'Above 200 SMA (Pass)' if playbook_res.close_above_sma200 else 'Below 200 SMA (Defensive)'} [SMA200: {playbook_res.sma200:,.1f}]" if playbook_res.sma200 else "Close vs 200 : N/A",
                    f"Lower BB (20): {'Penetrated (Pass)' if playbook_res.close_below_lower_bb else 'Inside (No Trigger)'} [Lower: {playbook_res.lower_bb:,.1f}]" if playbook_res.lower_bb else "Lower BB (20): N/A",
                    f"RSI(2)       : {playbook_res.rsi2:.1f} [{'Pass (<10)' if playbook_res.rsi2_below_10 else 'No'}]" if playbook_res.rsi2 is not None else "RSI(2)       : N/A",
                    f"Diagnosis    : {playbook_res.rationale}",
                    f"Target Exit  : {playbook_res.target_exit_price:,.1f} (20-day SMA)" if playbook_res.target_exit_price else "Target Exit  : N/A",
                    f"Stop-Loss    : {playbook_res.stop_loss_spot_price:,.1f} (1.5 ATR below entry low)" if playbook_res.stop_loss_spot_price else "Stop-Loss    : N/A",
                ]
                if playbook_res
                else []
            ),
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
