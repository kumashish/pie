"""Quantitative Exit Rules and Trade Lifecycle Management for Advisory Options Positions."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field

from pie.market.trade_estimate import EstimatedTrade


class ExitReason(StrEnum):
    """Exit triggers for active option strategies."""

    REGIME_SHIFT = "🔴 Exit (Regime Shift)"
    DTE_EXPIRATION = "🟡 Exit (DTE < 10)"
    TAKE_PROFIT = "🎯 Take Profit"
    STOP_LOSS = "⚠️ Stop Loss"
    NONE = "Active"


class ClosedTradeRecord(BaseModel):
    """Record of a closed or exited trade."""

    symbol: str
    market: str
    strategy_type: str
    strategy_name: str
    strategy_structure: str
    entry_date: str
    closed_date: str
    exit_reason: str
    entry_score: float
    final_score: float


def calculate_dte(expiration: datetime | str, current_time: Optional[datetime] = None) -> int:
    """Calculate Days To Expiration (DTE)."""
    if current_time is None:
        current_time = datetime.now(UTC)
    if isinstance(expiration, str):
        # Format e.g. "2026-08-25" or "25-Aug-2026"
        for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                exp_dt = datetime.strptime(expiration, fmt)
                if exp_dt.tzinfo is None:
                    exp_dt = exp_dt.replace(tzinfo=UTC)
                break
            except ValueError:
                continue
        else:
            return 30  # Default assumption if unparseable
    else:
        exp_dt = expiration
        if exp_dt.tzinfo is None:
            exp_dt = exp_dt.replace(tzinfo=UTC)

    delta = (exp_dt.date() - current_time.date()).days
    return max(0, delta)


def evaluate_exit_condition(
    symbol: str,
    spot_price: float,
    expiration: datetime | str,
    current_regime: str,
    current_score: float,
    previous_regime: str,
    previous_strategy: str,
    estimated_trade: Optional[EstimatedTrade] = None,
    current_time: Optional[datetime] = None,
) -> tuple[bool, str]:
    """Evaluate whether an active trade should be closed.

    Returns:
        (should_exit: bool, reason_display: str)
    """
    dte = calculate_dte(expiration, current_time)

    # 1. DTE Rule: Exit if DTE <= 10 days to avoid gamma/pin risk
    if dte <= 10:
        return True, ExitReason.DTE_EXPIRATION.value

    # 2. Regime Shift Rule:
    # If strategy was Call Debit Spread / Bullish but regime switched to Bear/Strong Bear (score < 4.5)
    # If strategy was Put Debit Spread / Bearish but regime switched to Bull/Strong Bull (score > 5.5)
    strat_clean = previous_strategy.lower().replace("_", " ")
    regime_clean = current_regime.lower().replace("_", " ")

    if "call debit" in strat_clean and ("bear" in regime_clean or current_score < 4.5):
        return True, ExitReason.REGIME_SHIFT.value

    if "put debit" in strat_clean and ("bull" in regime_clean or current_score > 5.5):
        return True, ExitReason.REGIME_SHIFT.value

    # 3. Target Profit / Stop Loss evaluation based on trade legs
    if estimated_trade is not None and len(estimated_trade.legs) >= 2:
        long_leg = estimated_trade.legs[0]
        short_leg = estimated_trade.legs[1]

        # For Call Debit Spread: Target profit is near short strike
        if long_leg.right.value == "call" and spot_price >= short_leg.strike:
            return True, ExitReason.TAKE_PROFIT.value

        # For Put Debit Spread: Target profit is near short strike
        if long_leg.right.value == "put" and spot_price <= short_leg.strike:
            return True, ExitReason.TAKE_PROFIT.value

        # Stop loss check if spot price drops > 2x leg width away from long strike
        width = abs(short_leg.strike - long_leg.strike)
        if long_leg.right.value == "call" and spot_price < (long_leg.strike - width):
            return True, ExitReason.STOP_LOSS.value
        if long_leg.right.value == "put" and spot_price > (long_leg.strike + width):
            return True, ExitReason.STOP_LOSS.value

    return False, ExitReason.NONE.value
