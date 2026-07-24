"""Unit tests for quantitative exit rules and trade lifecycle engine."""

from datetime import UTC, datetime, timedelta

from pie.market.exit_rules import ExitReason, calculate_dte, evaluate_exit_condition


def test_calculate_dte():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)
    dte = calculate_dte(expiry, current_time=now)
    assert dte == 32

    # String format
    dte_str = calculate_dte("2026-08-03", current_time=now)
    assert dte_str == 10


def test_exit_on_dte_less_than_10():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 1, 12, 0, 0, tzinfo=UTC)  # 8 days DTE

    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4600.0,
        expiration=expiry,
        current_regime="bull",
        current_score=9.0,
        previous_regime="bull",
        previous_strategy="call_debit_spread",
        current_time=now,
    )
    assert should_exit is True
    assert reason == ExitReason.DTE_EXPIRATION.value


def test_exit_on_regime_shift():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)

    # Bullish strategy, but current regime shifted to bear with score 3.0
    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4600.0,
        expiration=expiry,
        current_regime="bear",
        current_score=3.0,
        previous_regime="bull",
        previous_strategy="call_debit_spread",
        current_time=now,
    )
    assert should_exit is True
    assert reason == ExitReason.REGIME_SHIFT.value


def test_active_trade_no_exit():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)

    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4600.0,
        expiration=expiry,
        current_regime="strong_bull",
        current_score=9.5,
        previous_regime="bull",
        previous_strategy="call_debit_spread",
        current_time=now,
    )
    assert should_exit is False
    assert reason == ExitReason.NONE.value
