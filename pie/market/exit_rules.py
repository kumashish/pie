"""Quantitative Exit Rules and Trade Lifecycle Management for Advisory Options Positions."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel

from pie.market.trade_estimate import EstimatedTrade


class ExitReason(StrEnum):
    """Exit triggers for active option strategies."""

    REGIME_SHIFT = "🔴 Exit (Regime Shift)"
    GAMMA_GATE = "🔴 Exit / Roll (14 DTE Gamma Gate)"
    FIRST_REVIEW = "🟡 Review / Roll (21 DTE First Review)"
    DTE_EXPIRATION = "🟡 Exit (DTE < 10)"
    TAKE_PROFIT = "🎯 Take Profit (50%+ Max Profit)"
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
    ema20: Optional[float] = None,
    unrealized_pnl: Optional[float] = None,
    net_credit: Optional[float] = None,
) -> tuple[bool, str]:
    """Evaluate whether an active trade should be closed or rolled under Loss Elimination Guardrails.

    Returns:
        (should_exit: bool, reason_display: str)
    """
    dte = calculate_dte(expiration, current_time)

    # 1. Gamma Risk Expiry Guardrail: Mandate exiting all option spreads at <= 21 DTE (or <= 14 DTE)
    if dte <= 10:
        return True, ExitReason.DTE_EXPIRATION.value
    if dte <= 14:
        return True, ExitReason.GAMMA_GATE.value
    if dte <= 21:
        return True, ExitReason.FIRST_REVIEW.value

    # 2. Dynamic Stop-Loss Rule: 1:1 Credit Loss Limit (Loss exceeds 100% of credit received)
    if unrealized_pnl is not None and net_credit is not None and net_credit > 0:
        if unrealized_pnl <= -net_credit:
            return True, ExitReason.STOP_LOSS.value

    # 3. Dynamic Take-Profit Rule: 50% Max Profit Target
    if unrealized_pnl is not None and net_credit is not None and net_credit > 0:
        if unrealized_pnl >= 0.50 * net_credit:
            return True, ExitReason.TAKE_PROFIT.value

    # 4. Short Strike / EMA20 Boundary Breach Rule
    strat_clean = previous_strategy.lower().replace("_", " ")
    regime_clean = current_regime.lower().replace("_", " ")

    is_bullish = any(b in strat_clean for b in ("bull", "credit spread", "credit", "call debit", "naked put", "jade lizard", "tradecraft"))
    is_bearish = any(b in strat_clean for b in ("bear", "put debit", "naked call"))

    if is_bullish and ema20 is not None and spot_price < ema20:
        return True, ExitReason.STOP_LOSS.value

    if is_bearish and ema20 is not None and spot_price > ema20:
        return True, ExitReason.STOP_LOSS.value

    # 5. Regime Shift Rule:
    if "call debit" in strat_clean and ("bear" in regime_clean or current_score < 4.5):
        return True, ExitReason.REGIME_SHIFT.value

    if "put debit" in strat_clean and ("bull" in regime_clean or current_score > 5.5):
        return True, ExitReason.REGIME_SHIFT.value

    # 6. Target Profit / Stop Loss evaluation based on trade legs
    if estimated_trade is not None and len(estimated_trade.legs) >= 1:
        strat_name = (
            estimated_trade.strategy.value
            if hasattr(estimated_trade.strategy, "value")
            else str(estimated_trade.strategy)
        ).lower()

        # Debit Spreads Target Profit: short strike reached/exceeded
        if len(estimated_trade.legs) >= 2:
            long_leg = estimated_trade.legs[0]
            short_leg = estimated_trade.legs[1]

            # For Call Debit Spread: Target profit is near or above short strike
            if long_leg.right.value == "call" and spot_price >= short_leg.strike:
                return True, ExitReason.TAKE_PROFIT.value

            # For Put Debit Spread: Target profit is near or below short strike
            if long_leg.right.value == "put" and spot_price <= short_leg.strike:
                return True, ExitReason.TAKE_PROFIT.value

        # Short leg breach check for Credit / Short strategies
        if "debit" not in strat_name:
            for leg in estimated_trade.legs:
                if leg.action.lower() in ("sell", "short"):
                    if leg.right.value == "put" and spot_price < leg.strike:
                        return True, ExitReason.STOP_LOSS.value
                    if leg.right.value == "call" and spot_price > leg.strike:
                        return True, ExitReason.STOP_LOSS.value

        if len(estimated_trade.legs) >= 2:
            long_leg = estimated_trade.legs[0]
            short_leg = estimated_trade.legs[1]
            width = abs(short_leg.strike - long_leg.strike)
            if long_leg.right.value == "call" and spot_price < (long_leg.strike - width):
                return True, ExitReason.STOP_LOSS.value
            if long_leg.right.value == "put" and spot_price > (long_leg.strike + width):
                return True, ExitReason.STOP_LOSS.value

    return False, ExitReason.NONE.value
