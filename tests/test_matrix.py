"""Unit tests for Regime Confluence Matrix, VIX Spiking Panic Filters, and Benchmark Alignment."""

from datetime import datetime
import pytest

from pie.market.strategy import StrategyType, score_all_strategies, select_strategy
from pie.market.trend.matrix import evaluate_regime_confluence, evaluate_vix_spiking
from pie.market.trend.models import ConfidenceScore, MarketRegime, TrendAnalysis, TrendScore


def create_analysis(
    regime: MarketRegime = MarketRegime.BULL,
    trend_score: float = 7.5,
    confidence: float = 1.0,
    indicator_values: dict | None = None,
) -> TrendAnalysis:
    return TrendAnalysis(
        symbol="SPY",
        timestamp=datetime(2026, 1, 1),
        trend_score=TrendScore(value=trend_score),
        confidence=ConfidenceScore(value=confidence),
        regime=regime,
        explanation="Test explanation",
        indicator_values=indicator_values or {},
    )


def test_vix_spiking_evaluator_triggers():
    # VIX > 28
    regime, spiking, msg = evaluate_vix_spiking(vix=30.0)
    assert spiking is True
    assert "28.0" in msg

    # 20-day VIX change >= +20% (passed as 0.25 -> 25%)
    regime, spiking, msg = evaluate_vix_spiking(vix=20.0, vix_change_20d=0.25)
    assert spiking is True
    assert "+25.0%" in msg

    # Normal VIX
    regime, spiking, msg = evaluate_vix_spiking(vix=18.0, vix_change_20d=0.05)
    assert spiking is False


def test_counter_benchmark_penalty_blocks_bullish_trades():
    an = create_analysis(MarketRegime.BULL, trend_score=7.5)
    # Benchmark is BEAR
    scores = score_all_strategies(an, iv_rank=50.0, benchmark_regime="BEAR")

    # Bullish strategies (Call Debit Spread, Credit Spread - Bull Put) should be heavily penalized
    assert scores[StrategyType.CALL_DEBIT_SPREAD].score < 25.0
    assert scores[StrategyType.CREDIT_SPREAD].score < 40.0
    assert scores[StrategyType.CREDIT_SPREAD].grade == "F (Unsuited)"


def test_counter_benchmark_penalty_blocks_bearish_trades():
    an = create_analysis(MarketRegime.BEAR, trend_score=2.5)
    # Benchmark is BULL
    scores = score_all_strategies(an, iv_rank=50.0, benchmark_regime="BULL")

    # Bearish strategies should be heavily penalized
    assert scores[StrategyType.PUT_DEBIT_SPREAD].score < 25.0
    assert scores[StrategyType.NAKED_CALL].score < 25.0


def test_vix_spiking_panic_disqualifies_debit_spreads_and_mandates_neutral_or_cash():
    an = create_analysis(MarketRegime.BULL, trend_score=7.5)

    # VIX > 28
    scores = score_all_strategies(an, iv_rank=70.0, vix=32.0)
    assert scores[StrategyType.CALL_DEBIT_SPREAD].score == 0.0
    assert scores[StrategyType.PUT_DEBIT_SPREAD].score == 0.0
    assert "Disqualified" in scores[StrategyType.CALL_DEBIT_SPREAD].rationale

    rec = select_strategy(an, iv_rank=70.0, vix=32.0)
    # Recommendation should mandate NEUTRAL Iron Condor / Iron Butterfly or NO_TRADE (Cash holding)
    assert rec.strategy in {StrategyType.IRON_CONDOR, StrategyType.IRON_BUTTERFLY, StrategyType.NO_TRADE}
    if rec.actionable:
        assert "VIX Spiking / Volatility Expansion Panic" in rec.rationale


def test_ema200_macro_and_ema20_momentum_penalties():
    # Price (90) is below EMA200 (100) and below EMA20 (95)
    indicators = {
        "last_price": 90.0,
        "EMA200": 100.0,
        "EMA20": 95.0,
        "EMA50": 98.0,
    }
    an = create_analysis(MarketRegime.BULL, trend_score=7.5, indicator_values=indicators)
    scores = score_all_strategies(an, iv_rank=50.0)

    # Bullish setups should be penalized heavily for breaking both macro trend (EMA200) and short-term momentum (EMA20)
    assert scores[StrategyType.CALL_DEBIT_SPREAD].score < 30.0
