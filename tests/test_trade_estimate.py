from datetime import date

from pie.market.strategy import StrategyRecommendation, StrategyType
from pie.market.trade_estimate import OptionRight, estimate_trade


def recommendation(strategy: StrategyType) -> StrategyRecommendation:
    return StrategyRecommendation(
        strategy=strategy, actionable=True, rationale="Test recommendation"
    )


def test_call_debit_spread_uses_spot_vix_and_monthly_expiry() -> None:
    trade = estimate_trade(
        "^NSEI",
        24000.0,
        15.0,
        recommendation(StrategyType.CALL_DEBIT_SPREAD),
        "live ^INDIAVIX",
        as_of=date(2026, 7, 24),
    )

    assert trade is not None
    assert trade.expiration == date(2026, 8, 25)
    assert trade.legs[0].right is OptionRight.CALL
    assert trade.legs[0].strike == 24000.0
    assert trade.legs[1].strike > trade.legs[0].strike
    assert trade.vix_source == "live ^INDIAVIX"
    assert any("EMA50" in rule for rule in trade.exit_strategy)


def test_put_debit_spread_places_short_leg_below_long_leg() -> None:
    trade = estimate_trade(
        "^NSEI",
        24000.0,
        15.0,
        recommendation(StrategyType.PUT_DEBIT_SPREAD),
        "fallback assumption",
        as_of=date(2026, 7, 24),
    )

    assert trade is not None
    assert trade.legs[0].right is OptionRight.PUT
    assert trade.legs[1].strike < trade.legs[0].strike


def test_no_trade_strategy_does_not_create_estimate() -> None:
    trade = estimate_trade(
        "^NSEI",
        24000.0,
        15.0,
        recommendation(StrategyType.NO_TRADE),
        "live ^INDIAVIX",
        as_of=date(2026, 7, 24),
    )

    assert trade is None


def test_third_friday_september_2026() -> None:
    from pie.market.trade_estimate import _third_friday, _select_expiration

    # Sept 1, 2026 is Tuesday. 1st Friday is Sept 4, 3rd Friday is Sept 18.
    assert _third_friday(2026, 9) == date(2026, 9, 18)

    # For US options (e.g. SPY) with target DTE ~37 starting 2026-08-12:
    # 2026-08-12 + 37 days = 2026-09-18
    exp = _select_expiration(date(2026, 8, 12), StrategyType.CALL_DEBIT_SPREAD, "SPY")
    assert exp == date(2026, 9, 18)


def test_credit_spread_short_strike_and_atr_wing_width() -> None:
    trade = estimate_trade(
        "SPY",
        500.0,
        15.0,
        recommendation(StrategyType.CREDIT_SPREAD),
        "live VIX",
        as_of=date(2026, 7, 24),
        atr14=5.0,
    )
    assert trade is not None
    # Short put strike selected around 15-20 Delta (approx 1.5 ATR / 1.0 expected move away)
    short_leg = [leg for leg in trade.legs if leg.action == "sell"][0]
    long_leg = [leg for leg in trade.legs if leg.action == "buy"][0]
    assert short_leg.strike <= 500.0 - 7.5  # 1.5 * atr14 = 7.5
    # Wing width calibrated to ATR (5.0)
    assert round(abs(short_leg.strike - long_leg.strike), 2) == 5.0
    # Short leg delta in 15-20 delta range (abs(delta) < 0.25)
    assert short_leg.delta is not None and abs(short_leg.delta) <= 0.25
    assert any("50% max profit" in rule for rule in trade.exit_strategy)
    assert any("21 days to expiry" in rule for rule in trade.exit_strategy)


def test_iron_condor_short_strikes_and_atr_wing_width() -> None:
    trade = estimate_trade(
        "SPY",
        500.0,
        15.0,
        recommendation(StrategyType.IRON_CONDOR),
        "live VIX",
        as_of=date(2026, 7, 24),
        atr14=5.0,
    )
    assert trade is not None
    # 4 legs: long put, short put, short call, long call
    assert len(trade.legs) == 4
    short_put = [leg for leg in trade.legs if leg.action == "sell" and leg.right == OptionRight.PUT][0]
    long_put = [leg for leg in trade.legs if leg.action == "buy" and leg.right == OptionRight.PUT][0]
    short_call = [leg for leg in trade.legs if leg.action == "sell" and leg.right == OptionRight.CALL][0]
    long_call = [leg for leg in trade.legs if leg.action == "buy" and leg.right == OptionRight.CALL][0]

    # Wing width calibrated to ATR (5.0)
    assert round(abs(short_put.strike - long_put.strike), 2) == 5.0
    assert round(abs(long_call.strike - short_call.strike), 2) == 5.0
    # Short put and call are OTM by at least 1.5 ATR (7.5)
    assert short_put.strike <= 500.0 - 7.5
    assert short_call.strike >= 500.0 + 7.5
    assert any("50% max profit" in rule for rule in trade.exit_strategy)
    assert any("21 days to expiry" in rule for rule in trade.exit_strategy)



def test_jade_lizard_short_strikes_and_atr_wing_width() -> None:
    trade = estimate_trade(
        "SPY",
        500.0,
        15.0,
        recommendation(StrategyType.JADE_LIZARD),
        "live VIX",
        as_of=date(2026, 7, 24),
        atr14=5.0,
    )
    assert trade is not None
    # 3 legs: short put, short call, long call
    assert len(trade.legs) == 3
    short_put = [leg for leg in trade.legs if leg.action == "sell" and leg.right == OptionRight.PUT][0]
    short_call = [leg for leg in trade.legs if leg.action == "sell" and leg.right == OptionRight.CALL][0]
    long_call = [leg for leg in trade.legs if leg.action == "buy" and leg.right == OptionRight.CALL][0]

    # Wing width calibrated to ATR (5.0)
    assert round(abs(long_call.strike - short_call.strike), 2) == 5.0
    # Short put & call 15-20 delta OTM
    assert short_put.strike <= 500.0 - 7.5
    assert short_call.strike >= 500.0 + 7.5
    assert any("50% max profit" in rule for rule in trade.exit_strategy)
def test_guardrail_metadata_and_dte_window() -> None:
    trade = estimate_trade(
        "SPY",
        500.0,
        15.0,
        recommendation(StrategyType.CREDIT_SPREAD),
        "live VIX",
        as_of=date(2026, 7, 24),
    )
    assert trade is not None
    assert trade.take_profit_rule == "50% Max Profit"
    assert "100% Credit Loss" in trade.stop_loss_rule or "1:1" in trade.stop_loss_rule
    assert trade.target_dte_window == "30-60 DTE"
    # Days to expiration must fall within 30-60 DTE window
    dte = (trade.expiration - date(2026, 7, 24)).days
    assert 30 <= dte <= 60



