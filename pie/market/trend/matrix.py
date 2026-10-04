"""Regime Confluence Matrix for macro market regimes, benchmark trend alignment, and VIX volatility filters."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from pie.market.trend.models import MarketRegime, TrendAnalysis


class VolatilityRegime(StrEnum):
    """VIX volatility regime classification."""

    LOW = "low"
    NORMAL = "normal"
    ELEVATED = "elevated"
    SPIKING_PANIC = "spiking_panic"


@dataclass(frozen=True, slots=True)
class RegimeConfluenceResult:
    """Outcome of regime matrix evaluation."""

    vix_regime: VolatilityRegime
    is_vix_spiking: bool
    bm_bull_penalty: float
    bm_bear_penalty: float
    ema200_bull_penalty: float
    ema200_bear_penalty: float
    ema20_bull_penalty: float
    ema20_bear_penalty: float
    disqualified_strategies: set[str]
    rationale: list[str]


def evaluate_vix_spiking(
    vix: float | None = None,
    vix_change_20d: float | None = None,
) -> tuple[VolatilityRegime, bool, str]:
    """Check whether VIX is in a spiking / volatility expansion panic regime.
    
    Trigger: VIX > 28.0 or 20-day VIX change >= +20% (+0.20 or 20.0).
    """
    if vix is None and vix_change_20d is None:
        return VolatilityRegime.NORMAL, False, "VIX data unavailable; defaulting to normal volatility."

    vix_val = vix if vix is not None else 20.0
    change_val = vix_change_20d if vix_change_20d is not None else 0.0

    # Normalize percentage change if passed as ratio (e.g. 0.25 -> 25%)
    change_pct = change_val * 100.0 if (-1.0 <= change_val <= 1.0 and change_val != 0.0) else change_val

    is_spiking = (vix_val > 28.0) or (change_pct >= 20.0)

    if is_spiking:
        reasons = []
        if vix_val > 28.0:
            reasons.append(f"VIX ({vix_val:.1f}) exceeds threshold 28.0")
        if change_pct >= 20.0:
            reasons.append(f"20-day VIX change ({change_pct:+.1f}%) exceeds +20%")
        msg = f"VIX Spiking / Volatility Expansion Panic: {', '.join(reasons)}."
        return VolatilityRegime.SPIKING_PANIC, True, msg

    if vix_val >= 22.0:
        return VolatilityRegime.ELEVATED, False, f"Elevated VIX ({vix_val:.1f})."
    if vix_val <= 14.0:
        return VolatilityRegime.LOW, False, f"Low VIX ({vix_val:.1f})."

    return VolatilityRegime.NORMAL, False, f"Normal VIX ({vix_val:.1f})."


def evaluate_benchmark_confluence(
    benchmark_regime: str | None = None,
) -> tuple[float, float, str]:
    """Calculate counter-benchmark penalties for directional trades.
    
    If benchmark is BEAR / STRONG_BEAR, heavily penalize bullish strategies (penalty: 80.0).
    If benchmark is BULL / STRONG_BULL, heavily penalize bearish strategies (penalty: 80.0).
    """
    if not benchmark_regime:
        return 0.0, 0.0, "No benchmark regime specified."

    bm_norm = benchmark_regime.lower()
    if bm_norm in {"bear", "strong_bear"}:
        return 80.0, 0.0, f"Benchmark is {bm_norm.upper()}: Heavily penalizing counter-trend bullish trades."
    elif bm_norm in {"bull", "strong_bull"}:
        return 0.0, 80.0, f"Benchmark is {bm_norm.upper()}: Heavily penalizing counter-trend bearish trades."

    return 0.0, 0.0, f"Benchmark is {bm_norm.upper()}: Neutral alignment."


def evaluate_ema_alignment(
    last_price: float | None = None,
    ema20: float | None = None,
    ema200: float | None = None,
) -> tuple[float, float, float, float, list[str]]:
    """Evaluate 30-60 DTE trade setup alignment with 200 EMA macro trend and 20 EMA short-term momentum.
    
    Macro Trend (200 EMA):
    - Bullish setup requires Price > EMA200. Penalty if below: 35.0.
    - Bearish setup requires Price < EMA200. Penalty if above: 35.0.

    Short-Term Momentum (20 EMA):
    - Bullish setup requires Price > EMA20. Penalty if below: 25.0.
    - Bearish setup requires Price < EMA20. Penalty if above: 25.0.
    """
    ema200_bull_pen = 0.0
    ema200_bear_pen = 0.0
    ema20_bull_pen = 0.0
    ema20_bear_pen = 0.0
    notes = []

    if last_price is not None and ema200 is not None:
        if last_price < ema200:
            ema200_bull_pen = 35.0
            notes.append(f"Price ({last_price:.2f}) below EMA200 macro trend ({ema200:.2f}): Bullish penalty applied.")
        else:
            ema200_bear_pen = 35.0
            notes.append(f"Price ({last_price:.2f}) above EMA200 macro trend ({ema200:.2f}): Bearish penalty applied.")

    if last_price is not None and ema20 is not None:
        if last_price < ema20:
            ema20_bull_pen = 25.0
            notes.append(f"Price ({last_price:.2f}) below EMA20 short-term momentum ({ema20:.2f}): Bullish momentum penalty applied.")
        else:
            ema20_bear_pen = 25.0
            notes.append(f"Price ({last_price:.2f}) above EMA20 short-term momentum ({ema20:.2f}): Bearish momentum penalty applied.")

    return ema200_bull_pen, ema200_bear_pen, ema20_bull_pen, ema20_bear_pen, notes


def evaluate_regime_confluence(
    analysis: TrendAnalysis,
    benchmark_regime: str | None = None,
    vix: float | None = None,
    vix_change_20d: float | None = None,
) -> RegimeConfluenceResult:
    """Evaluate full regime matrix confluence for market strategy scoring."""
    # Check VIX indicators from analysis if not explicitly provided
    vix_val = vix
    if vix_val is None:
        vix_val = analysis.indicator_values.get("VIX") or analysis.indicator_values.get("vix")

    vix_chg = vix_change_20d
    if vix_chg is None:
        vix_chg = analysis.indicator_values.get("VIX_20D_CHANGE") or analysis.indicator_values.get("vix_20d_change")

    vix_regime, is_spiking, vix_msg = evaluate_vix_spiking(vix_val, vix_chg)
    bm_bull_pen, bm_bear_pen, bm_msg = evaluate_benchmark_confluence(benchmark_regime)

    last_price = analysis.indicator_values.get("last_price")
    ema20 = analysis.indicator_values.get("EMA20")
    ema200 = analysis.indicator_values.get("EMA200")

    ema200_bull, ema200_bear, ema20_bull, ema20_bear, ema_notes = evaluate_ema_alignment(
        last_price=last_price, ema20=ema20, ema200=ema200
    )

    disqualified = set()
    rationale = [vix_msg, bm_msg] + ema_notes

    if is_spiking:
        # Disqualify directional debit spreads and cash swing trades in VIX panic mode
        disqualified.update({
            "call_debit_spread",
            "put_debit_spread",
            "cash_swing_long",
            "cash_swing_short",
        })

    return RegimeConfluenceResult(
        vix_regime=vix_regime,
        is_vix_spiking=is_spiking,
        bm_bull_penalty=bm_bull_pen,
        bm_bear_penalty=bm_bear_pen,
        ema200_bull_penalty=ema200_bull,
        ema200_bear_penalty=ema200_bear,
        ema20_bull_penalty=ema20_bull,
        ema20_bear_penalty=ema20_bear,
        disqualified_strategies=disqualified,
        rationale=rationale,
    )
