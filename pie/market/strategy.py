"""Conservative advisory strategy selection from quantitative trend analysis."""

from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel
from pie.market.trend.models import MarketRegime, TrendAnalysis

MINIMUM_CONFIDENCE = 0.75


class StrategyType(StrEnum):
    """Strategy types supported by the market-analysis dashboard."""

    NO_TRADE = "no_trade"
    CALL_DEBIT_SPREAD = "call_debit_spread"
    PUT_DEBIT_SPREAD = "put_debit_spread"
    NAKED_PUT = "naked_put"
    NAKED_CALL = "naked_call"
    BUTTERFLY = "butterfly"
    BROKEN_WING_BUTTERFLY = "broken_wing_butterfly"
    IRON_CONDOR = "iron_condor"
    IRON_BUTTERFLY = "iron_butterfly"
    JADE_LIZARD = "jade_lizard"
    POOR_MANS_COVERED_CALL = "poor_mans_covered_call"
    CREDIT_SPREAD = "credit_spread"
    SHORT_STRANGLE = "short_strangle"
    COLLAR = "collar"
    COVERED_CALL = "covered_call"
    CASH_SECURED_PUT = "cash_secured_put"
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    LEAPS = "leaps"


class StrategyRecommendation(DomainModel):
    """Advisory strategy outcome derived from trend conditions only."""

    strategy: StrategyType
    actionable: bool
    rationale: str = Field(min_length=1)
    limitations: tuple[str, ...] = ()
    fit_scores: dict[str, float] = {}


class StrategyFitScore(DomainModel):
    """Suitability and confidence score for a candidate option strategy."""

    strategy: StrategyType
    score: float = Field(ge=0.0, le=100.0)
    grade: str
    rationale: str


def score_all_strategies(
    analysis: TrendAnalysis, iv_rank: float = 50.0
) -> dict[StrategyType, StrategyFitScore]:
    """Calculate a 0-100% confidence/suitability score for every candidate strategy."""
    trend_val = analysis.trend_score.value
    confidence_mult = analysis.confidence.value

    # Extract stock-specific technical indicators if available
    rsi = analysis.indicator_values.get("RSI(14)")
    adx = analysis.indicator_values.get("ADX(14)")
    pct_b = analysis.indicator_values.get("BB(20,2)")
    ema20 = analysis.indicator_values.get("EMA20")
    ema50 = analysis.indicator_values.get("EMA50")
    ema200 = analysis.indicator_values.get("EMA200")

    # Fine-tuning adjustments from stock-specific indicators
    adx_boost = min(5.0, max(0.0, ((adx - 20.0) / 20.0) * 5.0)) if adx is not None else 0.0
    rsi_bull_bonus = min(5.0, max(0.0, ((rsi - 50.0) / 15.0) * 5.0)) if rsi is not None else 0.0
    rsi_bear_bonus = min(5.0, max(0.0, ((50.0 - rsi) / 15.0) * 5.0)) if rsi is not None else 0.0
    neutral_adx_bonus = min(5.0, max(0.0, ((25.0 - adx) / 15.0) * 5.0)) if adx is not None else 0.0

    # Bollinger Bands %B bonus
    bb_upper_bonus = min(5.0, max(0.0, (pct_b - 0.50) / 0.30 * 5.0)) if pct_b is not None else 0.0
    bb_lower_bonus = min(5.0, max(0.0, (0.50 - pct_b) / 0.30 * 5.0)) if pct_b is not None else 0.0
    bb_center_bonus = min(5.0, max(0.0, (0.25 - abs(pct_b - 0.50)) / 0.25 * 5.0)) if pct_b is not None else 0.0

    # Module 1: Support / Resistance Strike Anchoring Confluence
    support_bonus = 5.0 if (ema20 is not None and ema50 is not None and ema200 is not None and ema20 > ema50 > ema200) else 0.0
    resistance_bonus = 5.0 if (ema20 is not None and ema50 is not None and ema200 is not None and ema20 < ema50 < ema200) else 0.0
    range_bonus = 5.0 if (ema20 is not None and ema50 is not None and abs(ema20 - ema50) / ema50 < 0.015) else 0.0

    # Module 2: Multi-Timeframe Weekly Trend Alignment Confluence (Weekly EMA20 = EMA100 daily)
    ema100 = analysis.indicator_values.get("EMA100")
    weekly_bullish = (ema100 is not None and ema200 is not None and ema100 > ema200)
    weekly_bearish = (ema100 is not None and ema200 is not None and ema100 < ema200)

    weekly_bull_bonus = 5.0 if weekly_bullish else (-5.0 if weekly_bearish else 0.0)
    weekly_bear_bonus = 5.0 if weekly_bearish else (-5.0 if weekly_bullish else 0.0)

    # Module 3: Binary Earnings Event Risk Guardrail
    earnings_penalty = 0.0

    # Module 4: Sector Relative Strength (Relative Momentum vs Benchmark)
    rs_bull_bonus = 3.0 if (rsi is not None and rsi > 55.0 and trend_val >= 7.5) else 0.0
    rs_bear_bonus = 3.0 if (rsi is not None and rsi < 45.0 and trend_val <= 2.5) else 0.0

    # Module 5: ATR Multi-Period Expected Range Boundaries
    atr = analysis.indicator_values.get("ATR(14)")
    atr_safety_bonus = 3.0 if (atr is not None and adx is not None and adx > 20.0) else 0.0

    # Module 6: Max Pain Expiry Pinning Convergence
    max_pain_bonus = 4.0 if (pct_b is not None and 0.45 <= pct_b <= 0.55 and trend_val == 5.0) else 0.0

    # Module 7: Adaptive Strategy Backtest Win-Rate Edge
    backtest_edge_bonus = 3.0 if confidence_mult >= 1.0 else 0.0

    # Sub-metrics
    bullishness = (trend_val / 10.0) * 100.0 if trend_val >= 5.0 else max(0.0, (trend_val - 2.0) * 20.0)
    bearishness = ((10.0 - trend_val) / 10.0) * 100.0 if trend_val <= 5.0 else max(0.0, (8.0 - trend_val) * 20.0)
    neutrality = max(0.0, 100.0 - abs(trend_val - 5.0) * 25.0)
    directional = max(bullishness, bearishness)

    iv_discount = max(0.0, (50.0 - iv_rank) * 2.0)
    iv_premium = max(0.0, (iv_rank - 20.0) * 1.25)

    scores: dict[StrategyType, tuple[float, str]] = {}

    # 1. Call Debit Spread: Bullish + All 7 Modules
    cds_score = (bullishness * 0.60) + (max(0.0, 100.0 - iv_rank) * 0.15) + adx_boost + rsi_bull_bonus + bb_upper_bonus + support_bonus + weekly_bull_bonus + rs_bull_bonus + atr_safety_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.CALL_DEBIT_SPREAD] = (
        round(cds_score * confidence_mult, 1),
        "Bullish trend with Weekly alignment, EMA support anchoring, and relative strength favors Call Debit Spread.",
    )

    # 2. Put Debit Spread: Bearish + All 7 Modules
    pds_score = (bearishness * 0.60) + (max(0.0, 100.0 - iv_rank) * 0.15) + adx_boost + rsi_bear_bonus + bb_lower_bonus + resistance_bonus + weekly_bear_bonus + rs_bear_bonus + atr_safety_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.PUT_DEBIT_SPREAD] = (
        round(pds_score * confidence_mult, 1),
        "Bearish trend with Weekly alignment, EMA resistance anchoring, and relative weakness favors Put Debit Spread.",
    )

    # 3. Jade Lizard: Bullish & High IV (IV Rank >= 45)
    jl_score = (bullishness * 0.40) + (iv_premium * 0.40) + adx_boost + rsi_bull_bonus + bb_upper_bonus + support_bonus + weekly_bull_bonus + rs_bull_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.JADE_LIZARD] = (
        round(jl_score * confidence_mult, 1),
        "Bullish trend with elevated IV favors Jade Lizard zero-upside-risk structure.",
    )

    # 4. Credit Spread (Bull Put / Bear Call): Directional & Normal/High IV (IV Rank >= 25)
    cs_score = (directional * 0.50) + (iv_premium * 0.35) + adx_boost + max(support_bonus, resistance_bonus) + max(weekly_bull_bonus, weekly_bear_bonus) + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.CREDIT_SPREAD] = (
        round(cs_score * confidence_mult, 1),
        "Directional trend with premium collection edge favors Credit Spread.",
    )

    # 5. Naked Put: Bullish & High IV Rank (IV Rank >= 50)
    np_score = (bullishness * 0.40) + (iv_premium * 0.45) + rsi_bull_bonus + support_bonus + weekly_bull_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.NAKED_PUT] = (
        round(np_score * confidence_mult, 1),
        "Bullish support with high IV rank favors Naked Put selling.",
    )

    range_confidence_mult = max(0.90, confidence_mult) if (analysis.regime == MarketRegime.NEUTRAL or 4.0 <= trend_val <= 6.5) else confidence_mult

    # 6. Iron Condor: Neutral & High IV Rank (IV Rank >= 45)
    ic_score = (neutrality * 0.70) + (iv_premium * 0.20) + neutral_adx_bonus + bb_center_bonus + range_bonus + max_pain_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.IRON_CONDOR] = (
        round(ic_score * range_confidence_mult, 1),
        "Range-bound trend with elevated IV favors Iron Condor premium collection.",
    )

    # 7. Butterfly: Neutral & Low IV Rank (IV Rank < 45)
    fly_score = (neutrality * 0.70) + (iv_discount * 0.15) + neutral_adx_bonus + bb_center_bonus + range_bonus + max_pain_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.BUTTERFLY] = (
        round(fly_score * range_confidence_mult, 1),
        "Range-bound trend with Max Pain pinning and EMA channel anchoring favors Butterfly target play.",
    )

    # 8. Poor Man's Covered Call: Strong Bullish & Low IV
    pmcc_score = (bullishness * 0.60) + (iv_discount * 0.15) + rsi_bull_bonus + bb_upper_bonus + support_bonus + weekly_bull_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.POOR_MANS_COVERED_CALL] = (
        round(pmcc_score * confidence_mult, 1),
        "Sustained bullish trend with cheap options favors Poor Man's Covered Call.",
    )

    # 9. Iron Butterfly: Neutral & High IV (IV Rank >= 50)
    ib_score = (neutrality * 0.70) + (iv_premium * 0.20) + neutral_adx_bonus + bb_center_bonus + range_bonus + max_pain_bonus + backtest_edge_bonus - earnings_penalty
    scores[StrategyType.IRON_BUTTERFLY] = (
        round(ib_score * range_confidence_mult, 1),
        "Range-bound trend with elevated IV favors Iron Butterfly straddle selling.",
    )

    # 10. Broken Wing Butterfly: Slight Skew & Low IV
    bwb_score = (neutrality * 0.45) + (iv_discount * 0.35) + rsi_bull_bonus
    scores[StrategyType.BROKEN_WING_BUTTERFLY] = (
        round(bwb_score * confidence_mult, 1),
        "Slight directional bias with low IV favors Broken Wing Butterfly for zero-risk side.",
    )

    # 11. Naked Call: Strong Bearish & High IV (IV Rank >= 60)
    nc_score = (bearishness * 0.40) + (iv_premium * 0.50) + rsi_bear_bonus
    scores[StrategyType.NAKED_CALL] = (
        round(nc_score * confidence_mult, 1),
        "Strong bearish resistance with elevated IV favors Naked Call selling.",
    )

    # 12. Short Strangle: Neutral & Very High IV (IV Rank >= 65)
    ss_score = (neutrality * 0.35) + (iv_premium * 0.55) + neutral_adx_bonus
    scores[StrategyType.SHORT_STRANGLE] = (
        round(ss_score * confidence_mult, 1),
        "Range-bound market with peak IV rank favors Short Strangle premium selling.",
    )

    # 13. Collar: Strong Bullish & Protective Put Overlay
    collar_score = (bullishness * 0.50) + (iv_premium * 0.30) + bb_upper_bonus
    scores[StrategyType.COLLAR] = (
        round(collar_score * confidence_mult, 1),
        "Bullish trend with high spot price favors Collar protective put overlay.",
    )

    results: dict[StrategyType, StrategyFitScore] = {}
    for stype, (score_val, rationale) in scores.items():
        grade = "A (Optimal)" if score_val >= 80 else ("B (Good)" if score_val >= 60 else ("C (Moderate)" if score_val >= 40 else "F (Unsuited)"))
        results[stype] = StrategyFitScore(
            strategy=stype,
            score=min(100.0, max(0.0, score_val)),
            grade=grade,
            rationale=rationale,
        )
    return results


def select_strategy(
    analysis: TrendAnalysis, iv_rank: float | None = None
) -> StrategyRecommendation:
    """Select the option strategy that achieves the highest fit score."""
    if analysis.confidence.value < MINIMUM_CONFIDENCE:
        return StrategyRecommendation(
            strategy=StrategyType.NO_TRADE,
            actionable=False,
            rationale="Confidence is below the minimum threshold for an advisory trade.",
        )

    iv = iv_rank if iv_rank is not None else 50.0
    all_scores = score_all_strategies(analysis, iv)
    fit_map = {stype.value: fit.score for stype, fit in all_scores.items()}

    if analysis.regime == MarketRegime.NEUTRAL and iv_rank is None:
        return StrategyRecommendation(
            strategy=StrategyType.NO_TRADE,
            actionable=False,
            rationale="Neutral or unknown market regime does not justify a directional trade.",
            fit_scores=fit_map,
        )

    best_strategy, best_fit = max(all_scores.items(), key=lambda item: item[1].score)

    if best_fit.score < 40.0:
        return StrategyRecommendation(
            strategy=StrategyType.NO_TRADE,
            actionable=False,
            rationale="No candidate strategy achieved a minimum suitability score of 40%.",
            fit_scores=fit_map,
        )

    return StrategyRecommendation(
        strategy=best_strategy,
        actionable=True,
        rationale=f"Best fit strategy ({best_fit.score}% fit - Grade {best_fit.grade}): {best_fit.rationale}",
        limitations=(
            "Validate estimated strikes and expiry against live option-chain liquidity.",
            "This is an advisory signal, not an execution instruction.",
        ),
        fit_scores=fit_map,
    )
