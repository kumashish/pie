from datetime import datetime

from pie.market.strategy import StrategyType, select_strategy
from pie.market.trend.models import ConfidenceScore, MarketRegime, TrendAnalysis, TrendScore


def analysis(regime: MarketRegime, confidence: float = 1.0) -> TrendAnalysis:
    score_map = {
        MarketRegime.STRONG_BULL: 9.0,
        MarketRegime.BULL: 7.0,
        MarketRegime.NEUTRAL: 5.0,
        MarketRegime.BEAR: 3.0,
        MarketRegime.STRONG_BEAR: 1.0,
        MarketRegime.UNKNOWN: 0.0,
    }
    score = score_map.get(regime, 5.0)
    return TrendAnalysis(
        symbol="SPY",
        timestamp=datetime(2026, 1, 1),
        trend_score=TrendScore(value=score),
        confidence=ConfidenceScore(value=confidence),
        regime=regime,
        explanation="Test explanation",
        indicator_values={},
    )


def test_bullish_regime_recommends_credit_spread() -> None:
    recommendation = select_strategy(analysis(MarketRegime.BULL))

    assert recommendation.strategy is StrategyType.CREDIT_SPREAD
    assert recommendation.actionable is True


def test_bearish_regime_recommends_credit_spread() -> None:
    recommendation = select_strategy(analysis(MarketRegime.BEAR))

    assert recommendation.strategy is StrategyType.CREDIT_SPREAD
    assert recommendation.actionable is True


def test_neutral_regime_returns_no_trade() -> None:
    recommendation = select_strategy(analysis(MarketRegime.NEUTRAL))

    assert recommendation.strategy is StrategyType.NO_TRADE
    assert recommendation.actionable is False


def test_low_confidence_returns_no_trade() -> None:
    recommendation = select_strategy(analysis(MarketRegime.STRONG_BULL, confidence=0.5))

    assert recommendation.strategy is StrategyType.NO_TRADE


def test_credit_structure_scores_higher_than_naked_trades() -> None:
    from pie.market.strategy import score_all_strategies

    an = analysis(MarketRegime.BULL)
    scores = score_all_strategies(an, iv_rank=60.0)

    # Defined-risk credit structures (Credit Spread, Jade Lizard) receive credit structure bonus
    # while unhedged naked put receives naked trade penalty
    assert scores[StrategyType.CREDIT_SPREAD].score > scores[StrategyType.NAKED_PUT].score
    assert scores[StrategyType.JADE_LIZARD].score > scores[StrategyType.NAKED_PUT].score


def test_rsi_overbought_triggers_mean_reversion_wait_guardrail() -> None:
    an = TrendAnalysis(
        symbol="SPY",
        timestamp=datetime(2026, 1, 1),
        trend_score=TrendScore(value=8.0),
        confidence=ConfidenceScore(value=1.0),
        regime=MarketRegime.BULL,
        explanation="Test overbought RSI",
        indicator_values={"RSI(14)": 72.0},  # RSI > 65
    )
    rec = select_strategy(an, iv_rank=40.0)
    assert rec.actionable is False
    assert "Wait for Mean Reversion" in rec.rationale


def test_benchmark_bearish_penalizes_bullish_strategies() -> None:
    from pie.market.strategy import score_all_strategies

    an = TrendAnalysis(
        symbol="AAPL",
        timestamp=datetime(2026, 1, 1),
        trend_score=TrendScore(value=7.5),
        confidence=ConfidenceScore(value=1.0),
        regime=MarketRegime.BULL,
        explanation="Bullish stock",
        indicator_values={},
    )
    # Neutral benchmark vs Bearish benchmark
    scores_neutral_bm = score_all_strategies(an, iv_rank=50.0, benchmark_regime="neutral")
    scores_bearish_bm = score_all_strategies(an, iv_rank=50.0, benchmark_regime="bear")

    # Bullish Call Debit Spread score is lower when benchmark is bearish
    assert scores_bearish_bm[StrategyType.CALL_DEBIT_SPREAD].score < scores_neutral_bm[StrategyType.CALL_DEBIT_SPREAD].score


def test_vix_panic_filter_favors_defined_risk_over_naked_trades() -> None:
    from pie.market.strategy import score_all_strategies

    an = analysis(MarketRegime.BULL)
    # High VIX / IV rank panic scenario (IV rank = 85.0)
    scores_panic = score_all_strategies(an, iv_rank=85.0)

    # In panic high IV scenarios, defined risk (Credit Spread) is strongly favored over unhedged naked trades
    assert scores_panic[StrategyType.CREDIT_SPREAD].score > scores_panic[StrategyType.NAKED_PUT].score
    assert scores_panic[StrategyType.CREDIT_SPREAD].grade.startswith("A") or scores_panic[StrategyType.CREDIT_SPREAD].score >= 70.0


