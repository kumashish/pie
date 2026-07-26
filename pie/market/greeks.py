"""Black-Scholes Option Greeks calculation engine."""

import math
from dataclasses import dataclass


def _norm_cdf(x: float) -> float:
    """Cumulative distribution function for standard normal distribution."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    """Probability density function for standard normal distribution."""
    return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)


@dataclass(frozen=True, slots=True)
class OptionGreeks:
    """Calculated Black-Scholes Greeks for an option contract."""

    delta: float
    gamma: float
    theta: float
    vega: float


def calculate_greeks(
    spot: float,
    strike: float,
    dte: int,
    volatility: float,
    is_call: bool = True,
    risk_free_rate: float = 0.05,
) -> OptionGreeks:
    """Calculate Black-Scholes Delta, Gamma, Theta, and Vega.

    :param spot: Current underlying price.
    :param strike: Option strike price.
    :param dte: Days to expiration.
    :param volatility: Annualized volatility (e.g. 0.20 for 20%).
    :param is_call: True for Call option, False for Put.
    :param risk_free_rate: Annualized risk-free interest rate.
    """
    if dte <= 0 or volatility <= 0.0 or spot <= 0.0 or strike <= 0.0:
        return OptionGreeks(delta=0.50 if is_call else -0.50, gamma=0.0, theta=0.0, vega=0.0)

    t = max(1.0 / 365.0, dte / 365.0)
    sigma = max(0.01, volatility)
    r = risk_free_rate

    d1 = (math.log(spot / strike) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)

    pdf_d1 = _norm_pdf(d1)
    cdf_d1 = _norm_cdf(d1)
    cdf_d2 = _norm_cdf(d2)

    if is_call:
        delta = cdf_d1
        theta = (- (spot * pdf_d1 * sigma) / (2.0 * math.sqrt(t)) - r * strike * math.exp(-r * t) * cdf_d2) / 365.0
    else:
        delta = cdf_d1 - 1.0
        theta = (- (spot * pdf_d1 * sigma) / (2.0 * math.sqrt(t)) + r * strike * math.exp(-r * t) * _norm_cdf(-d2)) / 365.0

    gamma = pdf_d1 / (spot * sigma * math.sqrt(t))
    vega = (spot * math.sqrt(t) * pdf_d1) / 100.0  # Change per 1% IV change

    return OptionGreeks(
        delta=round(delta, 3),
        gamma=round(gamma, 5),
        theta=round(theta, 3),
        vega=round(vega, 3),
    )
