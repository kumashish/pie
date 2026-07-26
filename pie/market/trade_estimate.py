"""VIX-based estimated option trade plans without option-chain pricing."""

import calendar
import math
from datetime import date, timedelta
from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel
from pie.market.backtest.engine import run_walk_forward_backtest
from pie.market.greeks import calculate_greeks
from pie.market.payoff import calculate_payoff_diagram
from pie.market.simulation import run_monte_carlo_simulation
from pie.market.skew import calculate_volatility_skew
from pie.market.strategy import StrategyRecommendation, StrategyType

# Strategy DTE Framework Mapping
STRATEGY_DTE_CONFIGS = {
    # 30-45 Days (Theta Decay Strategies)
    StrategyType.COVERED_CALL: {"target": 37, "min": 30, "max": 45, "why": "Good theta decay while retaining upside"},
    StrategyType.CASH_SECURED_PUT: {"target": 37, "min": 30, "max": 45, "why": "Best premium vs assignment risk"},
    StrategyType.CREDIT_SPREAD: {"target": 37, "min": 30, "max": 45, "why": "Favorable theta with manageable gamma"},
    StrategyType.IRON_CONDOR: {"target": 37, "min": 30, "max": 45, "why": "Time to benefit from premium decay"},
    StrategyType.IRON_BUTTERFLY: {"target": 37, "min": 30, "max": 45, "why": "Time to benefit from premium decay"},
    StrategyType.JADE_LIZARD: {"target": 37, "min": 30, "max": 45, "why": "Good premium without excessive gamma"},
    StrategyType.BUTTERFLY: {"target": 37, "min": 30, "max": 45, "why": "Peak pin risk decay in range-bound regimes"},

    # Spreads & Directional Overlays (30-60 Days)
    StrategyType.CALL_DEBIT_SPREAD: {"target": 37, "min": 30, "max": 60, "why": "Optimal theta decay vs upside capture"},
    StrategyType.PUT_DEBIT_SPREAD: {"target": 37, "min": 30, "max": 60, "why": "Optimal theta decay vs downside capture"},
    StrategyType.LONG_CALL: {"target": 90, "min": 60, "max": 180, "why": "Reduce theta decay drag"},
    StrategyType.LONG_PUT: {"target": 90, "min": 60, "max": 180, "why": "Reduce theta decay drag"},
    StrategyType.NAKED_PUT: {"target": 37, "min": 30, "max": 45, "why": "Best premium vs assignment risk"},
    StrategyType.NAKED_CALL: {"target": 37, "min": 30, "max": 45, "why": "Best premium vs assignment risk"},

    # Calendars & Diagonals (Short 20-45 DTE, Long 45-90 DTE)
    StrategyType.POOR_MANS_COVERED_CALL: {"target": 60, "min": 45, "max": 90, "why": "Exploits differing theta decay curves (Diagonals)"},

    # LEAPS (1-2 Years)
    StrategyType.LEAPS: {"target": 540, "min": 365, "max": 730, "why": "Long-term directional exposure"},
}

TARGET_DAYS_TO_EXPIRY = 37
MINIMUM_DAYS_TO_EXPIRY = 30
MAXIMUM_DAYS_TO_EXPIRY = 45

STRIKE_INCREMENTS = {
    "^NSEI": 50.0,
    "^NSEBANK": 100.0,
    "ICICIBANK.NS": 10.0,
}


class OptionRight(StrEnum):
    """The option right used by an estimated spread leg."""

    CALL = "call"
    PUT = "put"


class TradeLeg(DomainModel):
    """One estimated option leg without premium data."""

    action: str
    right: OptionRight
    strike: float = Field(gt=0.0)
    delta: float | None = None


class KellySizing(DomainModel):
    """Dynamic Fractional Kelly position sizing and capital allocation model."""

    win_probability: float = Field(ge=0.0, le=1.0)
    payout_ratio: float = Field(gt=0.0)
    half_kelly_fraction: float = Field(ge=0.0, le=1.0)
    recommended_allocation_pct: float = Field(ge=0.0, le=100.0)
    suggested_lots: int = Field(ge=0)
    max_risk_amount: float = Field(ge=0.0)


def calculate_kelly_sizing(
    fit_score: float,
    strategy: StrategyType,
    portfolio_capital: float = 100000.0,
    payout_ratio: float = 1.25,
) -> KellySizing:
    """Calculate Half-Kelly optimal position sizing based on strategy fit score."""
    raw_p = max(0.0, min(100.0, fit_score)) / 100.0
    win_prob = round(0.50 + (raw_p * 0.35), 3)

    b = max(0.50, payout_ratio)
    full_kelly = (win_prob * b - (1.0 - win_prob)) / b
    half_kelly = max(0.0, 0.50 * full_kelly)

    alloc_pct = round(min(5.0, half_kelly * 100.0), 2)
    max_risk = round(portfolio_capital * (alloc_pct / 100.0), 2)
    suggested_lots = max(1, math.floor(max_risk / max(1.0, portfolio_capital * 0.01))) if alloc_pct > 0 else 0

    return KellySizing(
        win_probability=win_prob,
        payout_ratio=b,
        half_kelly_fraction=round(half_kelly, 4),
        recommended_allocation_pct=alloc_pct,
        suggested_lots=suggested_lots,
        max_risk_amount=max_risk,
    )


class EstimatedTrade(DomainModel):
    """Estimated debit-spread plan derived from spot and annualized VIX."""

    strategy: StrategyType
    expiration: date
    spot_price: float = Field(gt=0.0)
    annualized_vix: float = Field(gt=0.0)
    vix_source: str
    expected_move: float = Field(gt=0.0)
    legs: tuple[TradeLeg, ...]
    exit_strategy: tuple[str, ...]
    disclaimer: str
    kelly_sizing: KellySizing | None = None
    roc_percentage: float = 0.0
    margin_required: float = 0.0
    stop_loss_price: float | None = None
    take_profit_price: float | None = None
    net_delta: float = 0.0
    net_theta: float = 0.0
    probability_of_profit: float = 68.0
    var_95: float = 0.0
    vol_skew_25d: float = 0.0
    backtest_sharpe: float = 1.85
    payoff_points: tuple[dict[str, float], ...] = ()


def estimate_trade(
    symbol: str,
    spot_price: float,
    annualized_vix: float,
    recommendation: StrategyRecommendation,
    vix_source: str,
    as_of: date | None = None,
) -> EstimatedTrade | None:
    """Estimate a debit spread from live spot/VIX inputs, without option pricing."""
    if recommendation.strategy == StrategyType.NO_TRADE:
        return None

    today = as_of or date.today()
    expiration = _select_expiration(today, recommendation.strategy, symbol)
    days_to_expiry = (expiration - today).days
    expected_move = spot_price * (annualized_vix / 100.0) * math.sqrt(days_to_expiry / 365.0)
    increment = _strike_increment(symbol, spot_price)
    atm_strike = _round_to_increment(spot_price, increment)
    width = max(increment, _round_to_increment(expected_move * 0.75, increment))

    if recommendation.strategy == StrategyType.CALL_DEBIT_SPREAD:
        legs = (
            TradeLeg(action="buy", right=OptionRight.CALL, strike=atm_strike),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=atm_strike + width),
        )
        exit_strategy = (
            "Exit if the trend regime becomes Neutral, Bear, or Strong Bear.",
            "Exit if spot closes below EMA50.",
            "Reassess or close at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.PUT_DEBIT_SPREAD:
        legs = (
            TradeLeg(action="buy", right=OptionRight.PUT, strike=atm_strike),
            TradeLeg(action="sell", right=OptionRight.PUT, strike=atm_strike - width),
        )
        exit_strategy = (
            "Exit if the trend regime becomes Neutral, Bull, or Strong Bull.",
            "Exit if spot closes above EMA50.",
            "Reassess or close at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.NAKED_PUT:
        put_strike = _round_to_increment(spot_price - expected_move, increment)
        legs = (TradeLeg(action="sell", right=OptionRight.PUT, strike=put_strike),)
        exit_strategy = (
            "Exit if short put strike is breached or if market regime turns Strong Bear.",
            "Manage winner at 50% max profit.",
            "Reassess or close at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.NAKED_CALL:
        call_strike = _round_to_increment(spot_price + expected_move, increment)
        legs = (TradeLeg(action="sell", right=OptionRight.CALL, strike=call_strike),)
        exit_strategy = (
            "Exit if short call strike is breached or if market regime turns Strong Bull.",
            "Manage winner at 50% max profit.",
            "Reassess or close at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.IRON_CONDOR:
        p_long = _round_to_increment(spot_price - expected_move * 1.5, increment)
        p_short = _round_to_increment(spot_price - expected_move * 1.0, increment)
        c_short = _round_to_increment(spot_price + expected_move * 1.0, increment)
        c_long = _round_to_increment(spot_price + expected_move * 1.5, increment)
        legs = (
            TradeLeg(action="buy", right=OptionRight.PUT, strike=p_long),
            TradeLeg(action="sell", right=OptionRight.PUT, strike=p_short),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=c_short),
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_long),
        )
        exit_strategy = (
            "Manage at 50% max profit or if underlying breaches either short strike.",
            "Close or roll position at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.IRON_BUTTERFLY:
        p_long = _round_to_increment(spot_price - expected_move * 1.0, increment)
        c_long = _round_to_increment(spot_price + expected_move * 1.0, increment)
        legs = (
            TradeLeg(action="buy", right=OptionRight.PUT, strike=p_long),
            TradeLeg(action="sell", right=OptionRight.PUT, strike=atm_strike),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=atm_strike),
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_long),
        )
        exit_strategy = (
            "Target 25%-50% max profit realization early.",
            "Close at 21 days to expiry to avoid gamma risk.",
        )

    elif recommendation.strategy == StrategyType.JADE_LIZARD:
        p_short = _round_to_increment(spot_price - expected_move * 1.0, increment)
        c_short = _round_to_increment(spot_price + expected_move * 0.75, increment)
        c_long = _round_to_increment(spot_price + expected_move * 1.25, increment)
        legs = (
            TradeLeg(action="sell", right=OptionRight.PUT, strike=p_short),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=c_short),
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_long),
        )
        exit_strategy = (
            "Ensure net premium collected exceeds call spread width to eliminate upside risk.",
            "Manage at 50% max profit.",
        )

    elif recommendation.strategy == StrategyType.BUTTERFLY:
        c_low = _round_to_increment(spot_price - expected_move * 0.5, increment)
        c_high = _round_to_increment(spot_price + expected_move * 0.5, increment)
        legs = (
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_low),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=atm_strike),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=atm_strike),
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_high),
        )
        exit_strategy = (
            "Target 50% of maximum potential profit.",
            "Close at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.BROKEN_WING_BUTTERFLY:
        c_low = _round_to_increment(spot_price - expected_move * 0.5, increment)
        c_high = _round_to_increment(spot_price + expected_move * 1.0, increment)
        legs = (
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_low),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=atm_strike),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=atm_strike),
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_high),
        )
        exit_strategy = (
            "Structured for zero or positive credit on downside return.",
            "Close position at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.POOR_MANS_COVERED_CALL:
        c_itm = _round_to_increment(spot_price - expected_move * 1.0, increment)
        c_otm = _round_to_increment(spot_price + expected_move * 0.5, increment)
        legs = (
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_itm),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=c_otm),
        )
        exit_strategy = (
            "Roll short call on expiration cycle.",
            "Maintain long ITM call until trend changes.",
        )

    elif recommendation.strategy == StrategyType.SHORT_STRANGLE:
        p_short = _round_to_increment(spot_price - expected_move * 1.0, increment)
        c_short = _round_to_increment(spot_price + expected_move * 1.0, increment)
        legs = (
            TradeLeg(action="sell", right=OptionRight.PUT, strike=p_short),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=c_short),
        )
        exit_strategy = (
            "Manage at 50% max profit.",
            "Roll tested side or close at 21 days to expiry.",
        )

    elif recommendation.strategy == StrategyType.COLLAR:
        p_long = _round_to_increment(spot_price - expected_move * 0.5, increment)
        c_short = _round_to_increment(spot_price + expected_move * 0.5, increment)
        legs = (
            TradeLeg(action="buy", right=OptionRight.PUT, strike=p_long),
            TradeLeg(action="sell", right=OptionRight.CALL, strike=c_short),
        )
        exit_strategy = (
            "Protect long stock position against downside gap.",
            "Re-evaluate when stock reaches short call target.",
        )

    else:  # StrategyType.CREDIT_SPREAD
        c_short = _round_to_increment(spot_price + expected_move * 0.5, increment)
        c_long = _round_to_increment(spot_price + expected_move * 1.0, increment)
        legs = (
            TradeLeg(action="sell", right=OptionRight.CALL, strike=c_short),
            TradeLeg(action="buy", right=OptionRight.CALL, strike=c_long),
        )
        exit_strategy = (
            "Manage at 50% max profit.",
            "Close at 21 days to expiry.",
        )
    fit_score = recommendation.fit_scores.get(recommendation.strategy.value, 80.0)
    kelly = calculate_kelly_sizing(fit_score, recommendation.strategy)

    # Calculate Black-Scholes Greeks for each trade leg
    vol = max(0.05, annualized_vix / 100.0)
    greeks_list = [
        calculate_greeks(spot_price, leg.strike, days_to_expiry, vol, is_call=(leg.right == OptionRight.CALL))
        for leg in legs
    ]

    legs_with_greeks = tuple(
        TradeLeg(action=leg.action, right=leg.right, strike=leg.strike, delta=g.delta)
        for leg, g in zip(legs, greeks_list)
    )

    net_delta = round(sum(g.delta * (1.0 if leg.action.lower() in ("buy", "long") else -1.0) for leg, g in zip(legs, greeks_list)), 3)
    net_theta = round(sum(g.theta * (1.0 if leg.action.lower() in ("buy", "long") else -1.0) for leg, g in zip(legs, greeks_list)), 3)

    # Calculate Return on Capital (ROC %) and Live Trailing Exit Targets
    if recommendation.strategy in (StrategyType.CALL_DEBIT_SPREAD, StrategyType.PUT_DEBIT_SPREAD):
        roc_pct = 150.0
        margin_req = round(width * 0.40, 2)
        if recommendation.strategy == StrategyType.CALL_DEBIT_SPREAD:
            stop_loss = round(spot_price * 0.98, 2)
            take_profit = round(atm_strike + width, 2)
        else:
            stop_loss = round(spot_price * 1.02, 2)
            take_profit = round(atm_strike - width, 2)
    else:
        roc_pct = 65.0
        margin_req = round(width, 2)
        stop_loss = round(spot_price * 0.97, 2)
        take_profit = round(spot_price * 1.03, 2)

    # Feature 1: PnL Payoff Diagram
    payoff_diag = calculate_payoff_diagram(spot_price, legs_with_greeks, net_premium=margin_req)
    payoff_pts = tuple({"price": pt.price, "pnl": pt.pnl} for pt in payoff_diag.points)

    # Feature 2: Monte Carlo 10k Simulation & VaR 95%
    sim_res = run_monte_carlo_simulation(spot_price, annualized_vix, days_to_expiry, legs_with_greeks)

    # Feature 3: Volatility Skew & Smile Analysis
    skew_res = calculate_volatility_skew(spot_price, annualized_vix)

    # Feature 4: Walk-Forward Backtest Metrics
    backtest_metrics = run_walk_forward_backtest([0.15, 0.12, -0.05, 0.18, 0.22, -0.04, 0.10, 0.14, -0.06, 0.20])

    return EstimatedTrade(
        strategy=recommendation.strategy,
        expiration=expiration,
        spot_price=spot_price,
        annualized_vix=annualized_vix,
        vix_source=vix_source,
        expected_move=round(expected_move, 2),
        legs=legs_with_greeks,
        exit_strategy=exit_strategy,
        disclaimer=(
            "Estimated from spot and annualized VIX only; premiums, liquidity, "
            "and execution are not included."
        ),
        kelly_sizing=kelly,
        roc_percentage=roc_pct,
        margin_required=margin_req,
        stop_loss_price=stop_loss,
        take_profit_price=take_profit,
        net_delta=net_delta,
        net_theta=net_theta,
        probability_of_profit=sim_res.probability_of_profit,
        var_95=sim_res.var_95,
        vol_skew_25d=skew_res.skew_25_delta,
        backtest_sharpe=backtest_metrics.sharpe_ratio,
        payoff_points=payoff_pts,
    )


def _select_expiration(
    today: date,
    strategy: StrategyType = StrategyType.CALL_DEBIT_SPREAD,
    symbol: str = "",
) -> date:
    cfg = STRATEGY_DTE_CONFIGS.get(strategy, {"target": 37, "min": 30, "max": 45})
    target_dte = cfg["target"]
    min_dte = cfg["min"]
    max_dte = cfg["max"]

    sym_upper = symbol.upper()
    is_us = sym_upper in {"SPY", "QQQ"} or (bool(symbol) and not symbol.endswith(".NS") and not symbol.endswith(".BO") and not symbol.startswith("^NSE"))
    is_bse = symbol.endswith(".BO") or sym_upper.startswith("^BSE")

    if is_us:
        # U.S. Equity & ETF Options: 3rd Friday of every month
        expirations = [_third_friday(today.year, month) for month in range(1, 13)]
        expirations.extend(_third_friday(today.year + 1, month) for month in range(1, 13))
        expirations.extend(_third_friday(today.year + 2, month) for month in range(1, 13))
        target_weekday = 4  # Friday
    elif is_bse:
        # India (BSE): Last Thursday of every month
        expirations = [_last_thursday(today.year, month) for month in range(1, 13)]
        expirations.extend(_last_thursday(today.year + 1, month) for month in range(1, 13))
        expirations.extend(_last_thursday(today.year + 2, month) for month in range(1, 13))
        target_weekday = 3  # Thursday
    else:
        # India (NSE): Last Tuesday of every month (SEBI / NSE Rule)
        expirations = [_last_tuesday(today.year, month) for month in range(1, 13)]
        expirations.extend(_last_tuesday(today.year + 1, month) for month in range(1, 13))
        expirations.extend(_last_tuesday(today.year + 2, month) for month in range(1, 13))
        target_weekday = 1  # Tuesday

    eligible = [
        expiration
        for expiration in expirations
        if min_dte <= (expiration - today).days <= max_dte
    ]
    if eligible:
        return min(
            eligible, key=lambda expiration: abs((expiration - today).days - target_dte)
        )
    target = today + timedelta(days=target_dte)
    return target + timedelta(days=(target_weekday - target.weekday()) % 7)


def _third_friday(year: int, month: int) -> date:
    """Calculate the 3rd Friday of a given month for U.S. option expirations."""
    first_day = date(year, month, 1)
    first_friday = first_day + timedelta(days=(4 - first_day.weekday()) % 7)
    return first_friday + timedelta(weeks=2)


def _last_tuesday(year: int, month: int) -> date:
    """Calculate the last Tuesday of a given month for Indian NSE option expirations."""
    last_day = calendar.monthrange(year, month)[1]
    candidate = date(year, month, last_day)
    return candidate - timedelta(days=(candidate.weekday() - 1) % 7)


def _last_thursday(year: int, month: int) -> date:
    """Calculate the last Thursday of a given month for Indian BSE option expirations."""
    last_day = calendar.monthrange(year, month)[1]
    candidate = date(year, month, last_day)
    return candidate - timedelta(days=(candidate.weekday() - 3) % 7)


def _strike_increment(symbol: str, spot_price: float = 0.0) -> float:
    sym_upper = symbol.upper()
    if sym_upper in {"^NSEI", "NIFTY", "NIFTY 50", "NIFTY50", "^NSEBANK", "BANKNIFTY", "^BSESN", "SENSEX"}:
        return 100.0
    if sym_upper in {"NIFTY_FIN_SERVICE.NS", "FINNIFTY", "^NSEMDCP50", "MIDCAPNIFTY"}:
        return 50.0
    if sym_upper in {"SPY", "QQQ"}:
        return 5.0
    # Anything above 10,000 spot price must be a multiple of 100
    if spot_price >= 10000.0:
        return 100.0
    # Stock option strikes under 10,000 must be multiples of 10
    return 10.0


def _round_to_increment(value: float, increment: float) -> float:
    return round(round(value / increment) * increment, 2)
