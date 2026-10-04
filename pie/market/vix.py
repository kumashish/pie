"""VIX index calculation algorithms (Option chain CBOE methodology & Realized Volatility estimator)."""

import math
from dataclasses import dataclass
from typing import Sequence

import polars as pl


@dataclass(frozen=True, slots=True)
class OptionContract:
    """Option contract snapshot for VIX calculation."""

    strike: float
    option_type: str  # "call" or "put"
    bid: float
    ask: float

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2.0


@dataclass(frozen=True, slots=True)
class VIXCalculationResult:
    """Calculated VIX index result."""

    vix: float
    forward_price: float
    strike_k0: float
    time_to_expiration_years: float
    risk_free_rate: float
    valid: bool
    reason: str | None = None


def calculate_cboe_vix(
    options: Sequence[OptionContract],
    time_to_expiration_years: float,
    risk_free_rate: float,
) -> VIXCalculationResult:
    """
    Calculate the VIX index using the CBOE model/formula from an option chain.

    Formula:
    VIX = 100 * sqrt( (2 / T) * sum( (delta_K_i / K_i^2) * e^(r*T) * Q(K_i) ) - (1 / T) * (F / K_0 - 1)^2 )
    
    where:
    - T: Time to expiration in years
    - r: Risk-free interest rate
    - F: Forward index price derived from min |Call_mid - Put_mid|
    - K_0: Strike price strictly below forward price F
    - Q(K_i): Option mid price (Put if K_i < K_0, Call if K_i > K_0, average of Call & Put at K_0)
    - delta_K_i: Half the distance between adjacent strikes
    """
    if time_to_expiration_years <= 0:
        return VIXCalculationResult(
            vix=0.0,
            forward_price=0.0,
            strike_k0=0.0,
            time_to_expiration_years=time_to_expiration_years,
            risk_free_rate=risk_free_rate,
            valid=False,
            reason="Time to expiration must be positive.",
        )

    if not options:
        return VIXCalculationResult(
            vix=0.0,
            forward_price=0.0,
            strike_k0=0.0,
            time_to_expiration_years=time_to_expiration_years,
            risk_free_rate=risk_free_rate,
            valid=False,
            reason="No options data provided.",
        )

    # Group options by strike
    strikes_map: dict[float, dict[str, float]] = {}
    for opt in options:
        if opt.mid <= 0:
            continue
        if opt.strike not in strikes_map:
            strikes_map[opt.strike] = {}
        strikes_map[opt.strike][opt.option_type.lower()] = opt.mid

    sorted_strikes = sorted(strikes_map.keys())
    if not sorted_strikes:
        return VIXCalculationResult(
            vix=0.0,
            forward_price=0.0,
            strike_k0=0.0,
            time_to_expiration_years=time_to_expiration_years,
            risk_free_rate=risk_free_rate,
            valid=False,
            reason="No valid option quotes with positive mid prices.",
        )

    # Step 1: Determine forward index price F by finding min diff between Call & Put
    min_diff = float("inf")
    f_strike = sorted_strikes[0]
    call_put_diff = 0.0

    for k in sorted_strikes:
        quotes = strikes_map[k]
        if "call" in quotes and "put" in quotes:
            diff = abs(quotes["call"] - quotes["put"])
            if diff < min_diff:
                min_diff = diff
                f_strike = k
                call_put_diff = quotes["call"] - quotes["put"]

    t = time_to_expiration_years
    r = risk_free_rate
    ert = math.exp(r * t)
    forward_price = f_strike + ert * call_put_diff

    # Step 2: Determine K_0 (first strike <= F)
    k_0_candidates = [k for k in sorted_strikes if k <= forward_price]
    k_0 = max(k_0_candidates) if k_0_candidates else sorted_strikes[0]

    # Step 3: Compute sum over strikes
    total_sum = 0.0
    num_strikes = len(sorted_strikes)

    for i, k in enumerate(sorted_strikes):
        quotes = strikes_map[k]
        
        # Determine delta_K_i
        if i == 0:
            delta_k = sorted_strikes[1] - sorted_strikes[0] if num_strikes > 1 else 1.0
        elif i == num_strikes - 1:
            delta_k = sorted_strikes[-1] - sorted_strikes[-2]
        else:
            delta_k = (sorted_strikes[i + 1] - sorted_strikes[i - 1]) / 2.0

        # Select option price Q(K_i)
        if k < k_0:
            q_k = quotes.get("put", 0.0)
        elif k > k_0:
            q_k = quotes.get("call", 0.0)
        else:
            c = quotes.get("call", 0.0)
            p = quotes.get("put", 0.0)
            q_k = (c + p) / 2.0 if (c and p) else (c or p)

        if q_k > 0:
            total_sum += (delta_k / (k**2)) * ert * q_k

    # Step 4: Calculate variance sigma^2 and VIX
    variance = (2.0 / t) * total_sum - (1.0 / t) * ((forward_price / k_0 - 1.0) ** 2)

    if variance <= 0:
        return VIXCalculationResult(
            vix=0.0,
            forward_price=forward_price,
            strike_k0=k_0,
            time_to_expiration_years=t,
            risk_free_rate=r,
            valid=False,
            reason="Calculated variance is non-positive.",
        )

    vix = 100.0 * math.sqrt(variance)

    return VIXCalculationResult(
        vix=round(vix, 2),
        forward_price=round(forward_price, 4),
        strike_k0=k_0,
        time_to_expiration_years=t,
        risk_free_rate=r,
        valid=True,
    )


def calculate_realized_vix(
    data: pl.DataFrame,
    window: int = 30,
    annualization_factor: float = 252.0,
) -> float | None:
    """
    Calculate an estimated annualized VIX/volatility measure from price log returns.

    Never fills missing data with 0. Drops/filters nulls per project rules.
    """
    if "close" not in data.columns or data.height < window + 1:
        return None

    clean_data = data.select(pl.col("close").cast(pl.Float64, strict=False)).drop_nulls()
    if clean_data.height < window + 1:
        return None

    log_returns = (
        clean_data.with_columns(
            log_return=(pl.col("close") / pl.col("close").shift(1)).log()
        )
        .get_column("log_return")
        .drop_nulls()
    )

    if log_returns.len() < window:
        return None

    recent_returns = log_returns.tail(window)
    std_dev = recent_returns.std()

    if std_dev is None or math.isnan(std_dev):
        return None

    realized_vol = float(std_dev * math.sqrt(annualization_factor) * 100.0)
    return round(realized_vol, 2)


def fetch_live_vix(symbol: str = "^INDIAVIX") -> float | None:
    """
    Fetch the live VIX value directly from market data provider for a given ticker symbol.

    Defaults to "^INDIAVIX" for Indian markets. Returns None if provider fails.
    """
    from pie.providers.yahoo import UrllibHTTPClient, YahooFinanceProvider

    try:
        provider = YahooFinanceProvider(UrllibHTTPClient())
        df = provider.fetch_history(symbol, period="5d", interval="1d")
        if df.height > 0 and "close" in df.columns:
            val = float(df.get_column("close").tail(1).item())
            return round(val, 2)
    except Exception:
        pass
    return None

