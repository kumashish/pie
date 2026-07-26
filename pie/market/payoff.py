"""Option Strategy PnL Payoff Diagram Generator."""

from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class PayoffPoint:
    price: float
    pnl: float


@dataclass(frozen=True, slots=True)
class PayoffDiagram:
    points: tuple[PayoffPoint, ...]
    max_profit: float
    max_loss: float
    breakeven_prices: tuple[float, ...]
    current_pnl: float


def calculate_payoff_diagram(
    spot_price: float,
    legs: Sequence[Any],
    net_premium: float = 0.0,
    steps: int = 50,
) -> PayoffDiagram:
    """Generate PnL payoff points across a +/- 20% underlying price range."""
    min_price = max(1.0, spot_price * 0.80)
    max_price = spot_price * 1.20
    step_size = (max_price - min_price) / steps

    points = []
    breakevens = []
    prev_pnl = None
    prev_price = None

    for i in range(steps + 1):
        price = round(min_price + i * step_size, 2)
        total_pnl = -net_premium

        for leg in legs:
            right_val = str(getattr(leg, "right", "call")).lower()
            action_val = str(getattr(leg, "action", "buy")).lower()
            strike_val = float(getattr(leg, "strike", spot_price))

            is_call = right_val in ("call", "ce", "c")
            is_buy = action_val in ("buy", "long")

            if is_call:
                intrinsic = max(0.0, price - strike_val)
            else:
                intrinsic = max(0.0, strike_val - price)

            leg_pnl = intrinsic if is_buy else -intrinsic
            total_pnl += leg_pnl

        pnl_val = round(total_pnl, 2)
        points.append(PayoffPoint(price=price, pnl=pnl_val))

        # Check for breakeven crossing
        if prev_pnl is not None and ((prev_pnl < 0 <= pnl_val) or (prev_pnl > 0 >= pnl_val)):
            if prev_pnl != pnl_val:
                be_price = prev_price + (0.0 - prev_pnl) * (price - prev_price) / (pnl_val - prev_pnl)
                breakevens.append(round(be_price, 2))

        prev_pnl = pnl_val
        prev_price = price

    all_pnls = [p.pnl for p in points]
    max_profit = max(all_pnls)
    max_loss = min(all_pnls)

    # Calculate current PnL at spot
    current_pnl = 0.0
    for leg in legs:
        right_val = str(getattr(leg, "right", "call")).lower()
        action_val = str(getattr(leg, "action", "buy")).lower()
        strike_val = float(getattr(leg, "strike", spot_price))

        is_call = right_val in ("call", "ce", "c")
        is_buy = action_val in ("buy", "long")

        intrinsic = max(0.0, spot_price - strike_val) if is_call else max(0.0, strike_val - spot_price)
        current_pnl += intrinsic if is_buy else -intrinsic

    return PayoffDiagram(
        points=tuple(points),
        max_profit=max_profit,
        max_loss=max_loss,
        breakeven_prices=tuple(sorted(set(breakevens))),
        current_pnl=round(current_pnl - net_premium, 2),
    )
