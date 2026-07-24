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


def test_bullish_regime_recommends_call_debit_spread() -> None:
    recommendation = select_strategy(analysis(MarketRegime.BULL))

    assert recommendation.strategy is StrategyType.CALL_DEBIT_SPREAD
    assert recommendation.actionable is True


def test_bearish_regime_recommends_put_debit_spread() -> None:
    recommendation = select_strategy(analysis(MarketRegime.BEAR))

    assert recommendation.strategy is StrategyType.PUT_DEBIT_SPREAD
    assert recommendation.actionable is True


def test_neutral_regime_returns_no_trade() -> None:
    recommendation = select_strategy(analysis(MarketRegime.NEUTRAL))

    assert recommendation.strategy is StrategyType.NO_TRADE
    assert recommendation.actionable is False


def test_low_confidence_returns_no_trade() -> None:
    recommendation = select_strategy(analysis(MarketRegime.STRONG_BULL, confidence=0.5))

    assert recommendation.strategy is StrategyType.NO_TRADE
