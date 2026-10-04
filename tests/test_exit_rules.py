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


def test_exit_on_21_dte_first_review():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 14, 12, 0, 0, tzinfo=UTC)  # 21 days DTE

    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4600.0,
        expiration=expiry,
        current_regime="bull",
        current_score=8.5,
        previous_regime="bull",
        previous_strategy="credit_spread",
        current_time=now,
    )
    assert should_exit is True
    assert reason == ExitReason.FIRST_REVIEW.value


def test_exit_on_14_dte_gamma_gate():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 7, 12, 0, 0, tzinfo=UTC)  # 14 days DTE

    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4600.0,
        expiration=expiry,
        current_regime="bull",
        current_score=8.5,
        previous_regime="bull",
        previous_strategy="credit_spread",
        current_time=now,
    )
    assert should_exit is True
    assert reason == ExitReason.GAMMA_GATE.value


def test_exit_on_50_percent_take_profit_target():
    from pie.market.trade_estimate import EstimatedTrade, TradeLeg, OptionRight

    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)  # 32 days DTE

    # Mock Estimated Trade with call debit spread: Long 4500 Call, Short 4600 Call
    est_trade = EstimatedTrade(
        strategy="call_debit_spread",
        expiration=expiry.date(),
        spot_price=4600.0,
        annualized_vix=15.0,
        vix_source="test",
        expected_move=100.0,
        legs=(
            TradeLeg(action="buy", right=OptionRight.CALL, strike=4500.0),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=4600.0),
        ),
        exit_strategy=("Manage winner at 50% max profit target.",),
        disclaimer="test",
    )

    # Spot price reached short strike 4600.0 -> target profit reached
    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4620.0,
        expiration=expiry,
        current_regime="bull",
        current_score=8.5,
        previous_regime="bull",
        previous_strategy="call_debit_spread",
        estimated_trade=est_trade,
        current_time=now,
    )
    assert should_exit is True
    assert reason == ExitReason.TAKE_PROFIT.value


def test_exit_on_stop_loss_trigger():
    from pie.market.trade_estimate import EstimatedTrade, TradeLeg, OptionRight

    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)  # 32 days DTE

    # Call Debit Spread: Long 4500 Call, Short 4600 Call (Width = 100)
    # Stop loss trigger if spot < long_strike - width = 4500 - 100 = 4400
    est_trade = EstimatedTrade(
        strategy="call_debit_spread",
        expiration=expiry.date(),
        spot_price=4350.0,
        annualized_vix=15.0,
        vix_source="test",
        expected_move=100.0,
        legs=(
            TradeLeg(action="buy", right=OptionRight.CALL, strike=4500.0),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=4600.0),
        ),
        exit_strategy=("Stop Loss",),
        disclaimer="test",
    )

    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4350.0,
        expiration=expiry,
        current_regime="bull",
        current_score=7.0,
        previous_regime="bull",
        previous_strategy="call_debit_spread",
        estimated_trade=est_trade,
        current_time=now,
    )
    assert should_exit is True
    assert reason == ExitReason.STOP_LOSS.value


def test_exit_on_credit_loss_1to1_limit():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)

    # Loss exceeds 100% of credit received (-500 loss on +400 credit)
    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4500.0,
        expiration=expiry,
        current_regime="bull",
        current_score=7.0,
        previous_regime="bull",
        previous_strategy="credit_spread",
        current_time=now,
        unrealized_pnl=-500.0,
        net_credit=400.0,
    )
    assert should_exit is True
    assert reason == ExitReason.STOP_LOSS.value


def test_exit_on_ema20_boundary_breach():
    now = datetime(2026, 7, 24, 12, 0, 0, tzinfo=UTC)
    expiry = datetime(2026, 8, 25, 12, 0, 0, tzinfo=UTC)

    # Bullish strategy, spot 4450 closed below EMA20 4500
    should_exit, reason = evaluate_exit_condition(
        symbol="TITAN.NS",
        spot_price=4450.0,
        expiration=expiry,
        current_regime="bull",
        current_score=7.0,
        previous_regime="bull",
        previous_strategy="credit_spread",
        current_time=now,
        ema20=4500.0,
    )
    assert should_exit is True
    assert reason == ExitReason.STOP_LOSS.value


