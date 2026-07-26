"""Orchestration of deterministic, configuration-driven trend analysis."""

from collections.abc import Mapping
from dataclasses import dataclass

import polars as pl
import structlog

from pie.core.models import MarketSnapshot
from pie.market.indicators.base import IndicatorResult
from pie.market.trend.explanation import build_explanation
from pie.market.trend.models import TrendAnalysis
from pie.market.trend.rules import (
    ADXStrongRule,
    ATRIncreasingRule,
    EMA20AboveEMA50Rule,
    EMA50AboveEMA200Rule,
    HigherHighsRule,
    HigherLowsRule,
    PriceAboveEMA200Rule,
    RSIHealthyRule,
    TrendRule,
)
from pie.market.trend.scoring import calculate_confidence, calculate_trend_score, classify_regime

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class TrendEngine:
    """Evaluate market trend from a snapshot, indicators, and price history."""

    rules: tuple[TrendRule, ...]

    @classmethod
    def from_weights(cls, weights: Mapping[str, float]) -> "TrendEngine":
        """Create the independent rule set from configured rule weights."""
        structure_weight = weights["structure"] / 2.0
        return cls(
            rules=(
                PriceAboveEMA200Rule(weight=weights["ema200"]),
                EMA20AboveEMA50Rule(weight=weights["ema_cross"]),
                EMA50AboveEMA200Rule(weight=weights["ema_stack"]),
                RSIHealthyRule(weight=weights["rsi"]),
                ADXStrongRule(weight=weights["adx"]),
                ATRIncreasingRule(weight=weights["atr"]),
                HigherHighsRule(weight=structure_weight),
                HigherLowsRule(weight=structure_weight),
            )
        )

    def analyze(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> TrendAnalysis:
        """Evaluate all rules and construct one deterministic TrendAnalysis."""
        results = tuple(rule.evaluate(snapshot, indicators, history) for rule in self.rules)
        score = calculate_trend_score(results)
        confidence = calculate_confidence(indicators, results)
        indicator_values = {name: result.value for name, result in indicators.items()}
        rsi_val = indicator_values.get("RSI(14)")
        bb_val = indicator_values.get("BB(20,2)")
        if rsi_val is not None and bb_val is not None:
            synth_pcr = round(min(1.80, max(0.40, 1.0 + ((50.0 - rsi_val) / 50.0) * 0.50 + (0.50 - bb_val) * 0.40)), 2)
            indicator_values["Synthetic PCR"] = synth_pcr

        analysis = TrendAnalysis(
            symbol=snapshot.symbol,
            timestamp=snapshot.observed_at,
            trend_score=score,
            confidence=confidence,
            regime=classify_regime(score, confidence, results),
            explanation=build_explanation(score, results),
            indicator_values=indicator_values,
            passed_rules=tuple(result.name for result in results if result.passed),
            failed_rules=tuple(result.name for result in results if not result.passed),
        )
        logger.info(
            "trend_analysis_completed",
            symbol=analysis.symbol,
            score=analysis.trend_score.value,
            confidence=analysis.confidence.value,
            regime=analysis.regime,
        )
        return analysis
