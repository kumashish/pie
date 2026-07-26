"""Implied Volatility Skew & Smile Optimizer Engine."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class VolatilitySkewAnalysis:
    """Analysis of options volatility skew and strike placement optimization."""

    skew_25_delta: float
    skew_regime: str
    optimal_short_strike_offset_pct: float
    skew_adjustment_rationale: str


def calculate_volatility_skew(
    spot_price: float,
    annualized_vix: float,
    rsi: float | None = None,
    pct_b: float | None = None,
) -> VolatilitySkewAnalysis:
    """Estimate 25-Delta Volatility Skew (Put IV - Call IV) and optimize strike offsets.

    :param spot_price: Spot price of underlying.
    :param annualized_vix: VIX or IV percentile.
    :param rsi: 14-period Relative Strength Index.
    :param pct_b: Bollinger Bands %B.
    """
    rsi_val = rsi if rsi is not None else 50.0
    bb_val = pct_b if pct_b is not None else 0.50

    # Downside put skew rises when RSI is low or price is near lower Bollinger band
    skew_est = round(((50.0 - rsi_val) / 50.0) * 3.5 + (0.50 - bb_val) * 4.0, 2)

    if skew_est > 2.0:
        regime = "Heavy Downside Put Skew"
        offset = 0.03  # Shift short put strike 3% lower to capture peak put IV
        rationale = f"Heavy Put Skew (+{skew_est:.1f}%): Option market is over-hedging downside risk. Shift short put strike down 3% to capture peak Put IV premium."
    elif skew_est < -1.5:
        regime = "Upside Call Skew"
        offset = -0.02  # Shift short call strike 2% higher to capture peak call IV
        rationale = f"Upside Call Skew ({skew_est:.1f}%): Option market is bidding upside calls. Shift short call strike up 2% to sell peak Call IV premium."
    else:
        regime = "Symmetrical Skew"
        offset = 0.0
        rationale = f"Symmetrical Skew ({skew_est:.1f}%): Balanced IV surface across Call and Put wings."

    return VolatilitySkewAnalysis(
        skew_25_delta=skew_est,
        skew_regime=regime,
        optimal_short_strike_offset_pct=offset,
        skew_adjustment_rationale=rationale,
    )
