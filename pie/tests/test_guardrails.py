"""Unit tests for pie strategy guardrails, 30-60 DTE focus, exit rules, delta placement, and VIX panic filter."""

import unittest
from datetime import UTC, date, datetime

from pie.market.exit_rules import ExitReason, evaluate_exit_condition
from pie.market.strategy import (
    StrategyRecommendation,
    StrategyType,
    score_all_strategies,
    select_strategy,
)
from pie.market.trade_estimate import (
    STRATEGY_DTE_CONFIGS,
    EstimatedTrade,
    OptionRight,
    TradeLeg,
    _select_expiration,
    estimate_trade,
)
from pie.market.trend.models import (
    ConfidenceScore,
    MarketRegime,
    TrendAnalysis,
    TrendScore,
)


class TestStrategyGuardrails(unittest.TestCase):
    def test_30_60_dte_focus_and_target_selection(self):
        """Verify that strategies enforce 30-60 DTE focus and target ~37 DTE."""
        # 1. Check strategy DTE mapping configurations
        self.assertEqual(STRATEGY_DTE_CONFIGS[StrategyType.CREDIT_SPREAD]["min"], 30)
        self.assertEqual(STRATEGY_DTE_CONFIGS[StrategyType.CREDIT_SPREAD]["max"], 60)
        self.assertEqual(STRATEGY_DTE_CONFIGS[StrategyType.CREDIT_SPREAD]["target"], 37)

        self.assertEqual(STRATEGY_DTE_CONFIGS[StrategyType.CALL_DEBIT_SPREAD]["min"], 30)
        self.assertEqual(STRATEGY_DTE_CONFIGS[StrategyType.CALL_DEBIT_SPREAD]["max"], 60)

        self.assertEqual(STRATEGY_DTE_CONFIGS[StrategyType.PUT_DEBIT_SPREAD]["min"], 30)
        self.assertEqual(STRATEGY_DTE_CONFIGS[StrategyType.PUT_DEBIT_SPREAD]["max"], 60)

        # 2. Test expiration selection for SPY (US 3rd Friday) starting 2026-08-12
        exp_date = _select_expiration(date(2026, 8, 12), StrategyType.CREDIT_SPREAD, "SPY")
        dte = (exp_date - date(2026, 8, 12)).days
        self.assertTrue(30 <= dte <= 60)

    def test_21_dte_early_exit_rule(self):
        """Verify 21 DTE first review early exit trigger."""
        now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
        expiry = datetime(2026, 8, 14, 12, 0, 0, tzinfo=UTC)  # Exactly 21 days DTE

        should_exit, reason = evaluate_exit_condition(
            symbol="SPY",
            spot_price=500.0,
            expiration=expiry,
            current_regime="bull",
            current_score=8.0,
            previous_regime="bull",
            previous_strategy="credit_spread",
            current_time=now,
        )
        self.assertTrue(should_exit)
        self.assertEqual(reason, ExitReason.FIRST_REVIEW.value)

    def test_50_percent_max_profit_target_rule(self):
        """Verify 50% max profit target exit trigger and inclusion in trade estimate exit rules."""
        now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
        expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)  # 32 days DTE

        est_trade = EstimatedTrade(
            strategy=StrategyType.CALL_DEBIT_SPREAD,
            expiration=expiry.date(),
            spot_price=500.0,
            annualized_vix=15.0,
            vix_source="live VIX",
            expected_move=15.0,
            legs=(
                TradeLeg(action="buy", right=OptionRight.CALL, strike=500.0),
                TradeLeg(action="sell", right=OptionRight.CALL, strike=510.0),
            ),
            exit_strategy=("Manage winner at 50% max profit target.",),
            disclaimer="test",
        )

        # Spot price reaches short strike (510.0) -> profit target reached
        should_exit, reason = evaluate_exit_condition(
            symbol="SPY",
            spot_price=510.0,
            expiration=expiry,
            current_regime="bull",
            current_score=8.5,
            previous_regime="bull",
            previous_strategy="call_debit_spread",
            estimated_trade=est_trade,
            current_time=now,
        )
        self.assertTrue(should_exit)
        self.assertEqual(reason, ExitReason.TAKE_PROFIT.value)

    def test_15_20_delta_short_strike_placement(self):
        """Verify that short strike selection for credit trades targets 15-20 delta (~1.5 ATR / 1.0 expected move OTM)."""
        rec = StrategyRecommendation(
            strategy=StrategyType.CREDIT_SPREAD,
            actionable=True,
            rationale="Test credit spread recommendation",
            fit_scores={"credit_spread": 85.0},
        )
        trade = estimate_trade(
            symbol="SPY",
            spot_price=500.0,
            annualized_vix=16.0,
            recommendation=rec,
            vix_source="live VIX",
            as_of=date(2026, 7, 24),
            atr14=5.0,
        )
        self.assertIsNotNone(trade)
        # Identify short leg
        short_leg = [leg for leg in trade.legs if leg.action == "sell"][0]
        # Spot is 500, expected move / 1.5 ATR distance put short strike below 492.5
        self.assertLessEqual(short_leg.strike, 500.0 - 7.5)
        self.assertIsNotNone(short_leg.delta)
        # Delta magnitude for 15-20 delta strike should be <= 0.25 (typically 0.15 - 0.20)
        self.assertLessEqual(abs(short_leg.delta), 0.25)
        self.assertGreaterEqual(abs(short_leg.delta), 0.05)

    def test_vix_panic_filter(self):
        """Verify strategy selection response during high VIX / VIX panic scenarios."""
        an = TrendAnalysis(
            symbol="SPY",
            timestamp=datetime(2026, 1, 1),
            trend_score=TrendScore(value=7.5),
            confidence=ConfidenceScore(value=1.0),
            regime=MarketRegime.BULL,
            explanation="Bullish trend during high VIX",
            indicator_values={},
        )

        # High VIX scenario (IV rank = 85.0)
        panic_scores = score_all_strategies(an, iv_rank=85.0)

        # Defined-risk credit spread should remain highly rated due to premium collection
        self.assertGreater(panic_scores[StrategyType.CREDIT_SPREAD].score, panic_scores[StrategyType.NAKED_PUT].score)
        # Naked unhedged options suffer heavy penalty during panic volatility
        self.assertLess(panic_scores[StrategyType.NAKED_PUT].score, 70.0)

    def test_loss_avoidance_rsi_mean_reversion_guardrail(self):
        """Verify loss-avoidance RSI overbought/oversold entry delay guardrail."""
        overbought_analysis = TrendAnalysis(
            symbol="SPY",
            timestamp=datetime(2026, 1, 1),
            trend_score=TrendScore(value=8.5),
            confidence=ConfidenceScore(value=1.0),
            regime=MarketRegime.BULL,
            explanation="Strong trend but RSI overbought",
            indicator_values={"RSI(14)": 75.0},
        )
        rec = select_strategy(overbought_analysis, iv_rank=45.0)
        self.assertFalse(rec.actionable)
        self.assertIn("Wait for Mean Reversion", rec.rationale)


if __name__ == "__main__":
    unittest.main()
