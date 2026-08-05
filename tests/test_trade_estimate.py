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

