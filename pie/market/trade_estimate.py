"""VIX-based estimated option trade plans without option-chain pricing."""

import calendar
import math
from datetime import date, timedelta
from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel
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
    expiration = _select_expiration(today, recommendation.strategy)
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
    return EstimatedTrade(
        strategy=recommendation.strategy,
        expiration=expiration,
        spot_price=spot_price,
        annualized_vix=annualized_vix,
        vix_source=vix_source,
        expected_move=round(expected_move, 2),
        legs=legs,
        exit_strategy=exit_strategy,
        disclaimer=(
            "Estimated from spot and annualized VIX only; premiums, liquidity, "
            "and execution are not included."
        ),
    )


def _select_expiration(today: date, strategy: StrategyType = StrategyType.CALL_DEBIT_SPREAD) -> date:
    cfg = STRATEGY_DTE_CONFIGS.get(strategy, {"target": 37, "min": 30, "max": 45})
    target_dte = cfg["target"]
    min_dte = cfg["min"]
    max_dte = cfg["max"]

    expirations = [_last_tuesday(today.year, month) for month in range(1, 13)]
    expirations.extend(_last_tuesday(today.year + 1, month) for month in range(1, 13))
    expirations.extend(_last_tuesday(today.year + 2, month) for month in range(1, 13))

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
    return target + timedelta(days=(1 - target.weekday()) % 7)


def _last_tuesday(year: int, month: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    candidate = date(year, month, last_day)
    return candidate - timedelta(days=(candidate.weekday() - 1) % 7)


def _strike_increment(symbol: str, spot_price: float = 0.0) -> float:
    sym_upper = symbol.upper()
    if sym_upper in {"^NSEBANK", "BANKNIFTY"}:
        return 100.0
    if sym_upper in {"^NSEI", "NIFTY", "NIFTY 50"}:
        return 50.0
    if sym_upper in {"SPY", "QQQ"}:
        return 1.0
    # Anything above 10,000 spot price must be a multiple of 100
    if spot_price >= 10000.0:
        return 100.0
    # Stock option strikes under 10,000 must be multiples of 10
    return 10.0


def _round_to_increment(value: float, increment: float) -> float:
    return round(round(value / increment) * increment, 2)
