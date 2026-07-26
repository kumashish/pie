"""Monte Carlo 10,000 Path Price Simulation & VaR 95% Risk Engine."""

import math
import random
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(frozen=True, slots=True)
class SimulationResult:
    """Outcome of 10,000-path Monte Carlo simulation."""

    paths_simulated: int
    probability_of_profit: float
    expected_pnl: float
    var_95: float
    median_final_price: float
    simulated_5th_percentile_price: float
    simulated_95th_percentile_price: float


def run_monte_carlo_simulation(
    spot_price: float,
    annualized_vix: float,
    days_to_expiry: int,
    legs: Sequence[Any],
    num_paths: int = 10000,
    risk_free_rate: float = 0.05,
) -> SimulationResult:
    """Run 10,000 Geometric Brownian Motion (GBM) path simulations for PnL and VaR 95%."""
    if spot_price <= 0 or days_to_expiry <= 0 or num_paths <= 0:
        return SimulationResult(
            paths_simulated=0,
            probability_of_profit=0.50,
            expected_pnl=0.0,
            var_95=0.0,
            median_final_price=spot_price,
            simulated_5th_percentile_price=spot_price,
            simulated_95th_percentile_price=spot_price,
        )

    t = days_to_expiry / 365.0
    sigma = max(0.01, annualized_vix / 100.0)
    mu = risk_free_rate

    drift = (mu - 0.5 * sigma * sigma) * t
    vol_sqrt_t = sigma * math.sqrt(t)

    rng = random.Random(42)
    final_prices = []
    final_pnls = []

    for _ in range(num_paths):
        z = rng.gauss(0.0, 1.0)
        s_t = spot_price * math.exp(drift + vol_sqrt_t * z)
        final_prices.append(s_t)

        # Calculate PnL at expiration
        pnl = 0.0
        for leg in legs:
            right_val = str(getattr(leg, "right", "call")).lower()
            action_val = str(getattr(leg, "action", "buy")).lower()
            strike_val = float(getattr(leg, "strike", spot_price))

            is_call = right_val in ("call", "ce", "c")
            is_buy = action_val in ("buy", "long")

            intrinsic = max(0.0, s_t - strike_val) if is_call else max(0.0, strike_val - s_t)
            pnl += intrinsic if is_buy else -intrinsic

        final_pnls.append(pnl)

    sorted_prices = sorted(final_prices)
    sorted_pnls = sorted(final_pnls)

    profitable_paths = sum(1 for pnl in final_pnls if pnl > 0)
    pop = round((profitable_paths / num_paths) * 100.0, 1)
    expected_pnl = round(sum(final_pnls) / num_paths, 2)

    var_95_idx = int(num_paths * 0.05)
    var_95 = round(abs(sorted_pnls[var_95_idx]), 2) if sorted_pnls[var_95_idx] < 0 else 0.0

    p5_price = round(sorted_prices[int(num_paths * 0.05)], 2)
    p50_price = round(sorted_prices[int(num_paths * 0.50)], 2)
    p95_price = round(sorted_prices[int(num_paths * 0.95)], 2)

    return SimulationResult(
        paths_simulated=num_paths,
        probability_of_profit=pop,
        expected_pnl=expected_pnl,
        var_95=var_95,
        median_final_price=p50_price,
        simulated_5th_percentile_price=p5_price,
        simulated_95th_percentile_price=p95_price,
    )
