"""NIFTY Income Portfolio Playbook (v1.4) Signal Generation Engine.

Implements systematic signal generation, regime screening, and defined-risk trade structures:
1. Market & Instruments Universe:
   - Primary: NIFTY (^NSEI)
   - Selective: BANKNIFTY (^NSEBANK)
   - Liquidity-qualified: FINNIFTY (NIFTY_FIN_SERVICE.NS)
2. IV Regime Classification (Playbook Section 2):
   - Very Low (VIX < 12 / IVR < 20): Calendars, Diagonals, Broken-Wing Butterflies
   - Low (VIX 12-15 / IVR 20-40): Calendars, Risk-defined Iron Butterflies
   - Normal (VIX 15-20 / IVR 40-60): Credit Spreads, Covered Calls
   - Elevated (VIX 20-25 / IVR 60-80): Defined-Risk Condors, Credit Spreads
   - High / Unstable (VIX > 25 / IVR > 80): Smaller, Defined-Risk Positions (Capital Preservation)
3. NIFTY Mean-Reversion Strategy (Playbook Section 8):
   - Trend Guardrail: Enter only if daily close is above 200-day SMA (below it, stand aside / defensive).
   - Entry Trigger (all 5 required):
     (1) Daily close below lower Bollinger Band (20-day SMA, 2σ)
     (2) RSI(2) < 10 (extreme short-term pullback)
     (3) Daily close above 200-day SMA (structural uptrend intact)
     (4) Adequate liquidity/costs (index options, tight bid-ask)
     (5) Portfolio stress, margin, hedge and concentration limits pass
   - Structure: Monthly NIFTY Bull Put Spread (1:1 defined risk, ~0.30 short delta, protective wing).
   - Exit Criteria:
     - Target: Daily close touching 20-day SMA (mean-reversion achieved)
     - Stop Loss A: Spot closes > 1.5 ATR(14) below entry-day low
     - Stop Loss B: Loss reaches 1.5x - 2.0x initial credit received
     - Time / Greek Exit: Review / exit at DTE <= 14 or short absolute delta > 0.35
     - Profit Ladder: Review at 50%, take profit at 75%, close above 90%
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pie.core.models import DomainModel
from pie.market.indicators.base import IndicatorResult


# Permitted Playbook Index Universe
PLAYBOOK_UNIVERSE = {
    "^NSEI": "NIFTY 50 (Primary)",
    "^NSEBANK": "BANKNIFTY (Selective)",
    "NIFTY_FIN_SERVICE.NS": "FINNIFTY (Liquid)",
}


class PlaybookSignalStatus(StrEnum):
    """Playbook mean-reversion signal states."""

    TRIGGERED = "TRIGGERED"           # All 5 entry conditions satisfied: Bull Put Spread candidate
    WATCHLIST = "WATCHLIST"           # Dip in progress (RSI(2) < 25 or near lower band, close > 200 SMA)
    STAND_ASIDE = "STAND_ASIDE"       # Close below 200-day SMA: structural deterioration / defensive
    NEUTRAL = "NEUTRAL"               # Normal trend, no pullback condition
    INELIGIBLE = "INELIGIBLE"         # Instrument not in approved options universe


class IVRegime(StrEnum):
    """Playbook Section 2 Volatility Regimes."""

    VERY_LOW = "Very Low"             # VIX < 12 / IVR < 20
    LOW = "Low"                       # VIX 12-15 / IVR 20-40
    NORMAL = "Normal"                 # VIX 15-20 / IVR 40-60
    ELEVATED = "Elevated"             # VIX 20-25 / IVR 60-80
    HIGH_UNSTABLE = "High / Unstable" # VIX > 25 / IVR > 80


@dataclass(frozen=True, slots=True)
class IVRegimeAnalysis:
    """Volatility regime diagnosis and strategy mapping per Playbook Section 2."""

    regime: IVRegime
    vix: float
    iv_rank: float
    recommended_strategies: list[str]
    guidance: str


@dataclass(frozen=True, slots=True)
class PlaybookMeanReversionSignal:
    """Result of evaluating the NIFTY Mean-Reversion strategy per Playbook Section 8."""

    symbol: str
    status: PlaybookSignalStatus
    is_triggered: bool
    close_price: float
    sma200: float | None
    sma20: float | None
    sma20_slope: float | None
    lower_bb: float | None
    upper_bb: float | None
    pct_b: float | None
    rsi2: float | None
    rsi14: float | None
    atr14: float | None
    day_low: float | None
    
    # Conditions checklist
    close_above_sma200: bool
    close_below_lower_bb: bool
    rsi2_below_10: bool
    adequate_liquidity: bool
    risk_limits_pass: bool

    # Execution & Exit Parameters
    target_exit_price: float | None     # 20-day SMA
    stop_loss_spot_price: float | None  # Entry Day Low - 1.5 * ATR(14)
    strategy_name: str
    suggested_structure: str
    target_dte_range: str
    target_short_delta: str
    exit_rules: list[str]
    rationale: str
    high_52w: float | None = None
    dist_52w_pct: float | None = None
    actual_trade: str = ""
    warnings: list[str] = field(default_factory=list)


def classify_iv_regime(vix: float = 15.0, iv_rank: float = 50.0) -> IVRegimeAnalysis:
    """Classify current market volatility regime per Playbook Section 2."""
    if vix < 12.0 or iv_rank < 20.0:
        regime = IVRegime.VERY_LOW
        strategies = ["Calendars", "Diagonals", "Broken-Wing Butterflies"]
        guidance = "Very low IV: options are cheap. Prefer long vega / positive convexity structures (calendars/diagonals)."
    elif vix < 15.0 or iv_rank < 40.0:
        regime = IVRegime.LOW
        strategies = ["Calendars", "Risk-Defined Iron Butterflies"]
        guidance = "Low IV: favor tight risk-defined iron butterflies or debit diagonals; avoid wide unhedged premium selling."
    elif vix < 20.0 or iv_rank < 60.0:
        regime = IVRegime.NORMAL
        strategies = ["Credit Spreads", "Covered Calls", "Bull Put Spreads"]
        guidance = "Normal IV: optimal environment for systematic defined-risk credit spreads and covered calls with 30-45 DTE."
    elif vix <= 25.0 or iv_rank <= 80.0:
        regime = IVRegime.ELEVATED
        strategies = ["Defined-Risk Iron Condors", "Defined-Risk Credit Spreads"]
        guidance = "Elevated IV: rich option premiums. Use strictly defined-risk condors and spreads; widen wings."
    else:
        regime = IVRegime.HIGH_UNSTABLE
        strategies = ["Smaller Defined-Risk Spreads", "Deep-OTM Tail Hedging", "Capital Preservation"]
        guidance = "High/Unstable IV: market panic / tail risk elevated. Reduce sizing to <50% normal, enforce strict wings."

    return IVRegimeAnalysis(
        regime=regime,
        vix=round(vix, 2),
        iv_rank=round(iv_rank, 1),
        recommended_strategies=strategies,
        guidance=guidance,
    )


def evaluate_nifty_mean_reversion(
    symbol: str,
    last_price: float,
    indicators: dict[str, IndicatorResult],
    day_low: float | None = None,
    vix: float = 15.0,
    iv_rank: float = 50.0,
    is_liquid_fno: bool = True,
    risk_limits_passed: bool = True,
    actual_trade: str = "",
    high_52w: float | None = None,
    dist_52w_pct: float | None = None,
) -> PlaybookMeanReversionSignal:
    """Evaluate NIFTY Mean-Reversion Strategy Signal per Playbook Section 8."""
    # 1. Universe filter check
    is_approved_universe = symbol.upper() in PLAYBOOK_UNIVERSE or symbol.upper().startswith("^NSE")
    adequate_liquidity = is_approved_universe and is_liquid_fno

    # 2. Extract Technical Indicators
    # SMA200 (structural trend) - fallback to EMA200 if SMA200 not yet available
    sma200_res = indicators.get("SMA200") or indicators.get("EMA200")
    sma200_val = float(sma200_res.value) if sma200_res and sma200_res.value is not None else None

    # SMA20 & Slope
    sma20_res = indicators.get("SMA20")
    sma20_val = float(sma20_res.value) if sma20_res and sma20_res.value is not None else None
    sma20_slope = (
        float(sma20_res.metadata.get("slope_5d", 0.0))
        if sma20_res and hasattr(sma20_res, "metadata") and "slope_5d" in sma20_res.metadata
        else None
    )

    # Bollinger Bands (20, 2σ)
    bb_res = indicators.get("BB(20,2)")
    lower_bb = None
    upper_bb = None
    pct_b = None
    if bb_res and bb_res.valid:
        pct_b = float(bb_res.value) if bb_res.value is not None else None
        if hasattr(bb_res, "metadata"):
            lower_bb = float(bb_res.metadata.get("lower", 0.0)) or None
            upper_bb = float(bb_res.metadata.get("upper", 0.0)) or None
            if sma20_val is None and "middle" in bb_res.metadata:
                sma20_val = float(bb_res.metadata.get("middle", 0.0))

    # RSI(2) (ultra-short-term oversold) & RSI(14)
    rsi2_res = indicators.get("RSI(2)")
    rsi2_val = float(rsi2_res.value) if rsi2_res and rsi2_res.value is not None else None

    rsi14_res = indicators.get("RSI(14)")
    rsi14_val = float(rsi14_res.value) if rsi14_res and rsi14_res.value is not None else None

    # ATR(14)
    atr_res = indicators.get("ATR(14)")
    atr14_val = float(atr_res.value) if atr_res and atr_res.value is not None else None

    ref_day_low = day_low if day_low is not None else (last_price - (atr14_val * 0.5 if atr14_val else last_price * 0.005))

    # 3. Evaluate Core Playbook Conditions
    # Condition (1): Daily close below lower Bollinger Band (20-day SMA, 2σ)
    close_below_lower_bb = (
        (lower_bb is not None and last_price < lower_bb)
        or (pct_b is not None and pct_b < 0.0)
    )

    # Condition (2): RSI(2) < 10
    rsi2_below_10 = (rsi2_val is not None and rsi2_val < 10.0)

    # Condition (3): Close above 200-day SMA
    close_above_sma200 = (sma200_val is not None and last_price > sma200_val)

    # Calculate stop loss: Spot closes > 1.5 ATR(14) below entry-day low
    stop_loss_spot = round(ref_day_low - (1.5 * (atr14_val or (last_price * 0.01))), 2)
    target_exit = round(sma20_val, 2) if sma20_val is not None else round(last_price * 1.02, 2)

    # 4. Determine Signal Status
    warnings: list[str] = []
    if not is_approved_universe:
        status = PlaybookSignalStatus.INELIGIBLE
        rationale = f"{symbol} is not part of the approved Playbook F&O Index Universe (NIFTY/BANKNIFTY/FINNIFTY)."
    elif not close_above_sma200 and sma200_val is not None:
        status = PlaybookSignalStatus.STAND_ASIDE
        rationale = (
            f"Daily close ({last_price:,.2f}) is below 200-day SMA ({sma200_val:,.2f}). "
            "Per Playbook Section 8: Stand aside or remain defensive. Do NOT initiate bull put spreads."
        )
        warnings.append("Macro structural downtrend: 200 SMA breached. Long put spreads prohibited.")
    elif close_below_lower_bb and rsi2_below_10 and close_above_sma200 and adequate_liquidity and risk_limits_passed:
        status = PlaybookSignalStatus.TRIGGERED
        rationale = (
            f"⚡ NIFTY MEAN-REVERSION BUY TRIGGER: Daily close ({last_price:,.2f}) penetrated lower Bollinger Band "
            f"({lower_bb:,.2f}) with extreme oversold RSI(2)={rsi2_val:.1f} (< 10) while holding firmly above 200-day SMA "
            f"({sma200_val:,.2f}). Systematic entry for Monthly Defined-Risk Bull Put Spread qualified."
        )
    elif close_above_sma200 and ((rsi2_val is not None and rsi2_val < 25.0) or (pct_b is not None and pct_b < 0.20)):
        status = PlaybookSignalStatus.WATCHLIST
        rationale = (
            f"Dip Watchlist: Index is pulling back within primary uptrend (RSI(2)={rsi2_val if rsi2_val else 'N/A'}, "
            f"%B={pct_b if pct_b else 'N/A'}). Close remains above 200-day SMA ({sma200_val:,.2f}). "
            "Monitoring for full Bollinger touch and RSI(2) < 10 trigger."
        )
    else:
        status = PlaybookSignalStatus.NEUTRAL
        rationale = (
            f"Neutral Trend Context: Index price ({last_price:,.2f}) is above 200-day SMA ({sma200_val:,.2f}). "
            "No extreme mean-reversion oversold condition detected."
        )

    # Playbook Exit rules specification
    exit_rules = [
        f"Mean-Reversion Target Exit: Daily close touches 20-day SMA (~{target_exit:,.2f}).",
        f"Structural Stop-Loss: Daily close > 1.5 ATR(14) below entry-day low (Spot <= {stop_loss_spot:,.2f}).",
        "Credit Stop-Loss: Exit if structure loss exceeds 1.5x - 2.0x initial credit received.",
        "Gamma / Expiry Guardrail: Mandatory review and exit at DTE <= 14 or if short put delta expands > 0.35.",
        "Profit Management Ladder: Review closing at 50% max profit; harvest gains systematically at 75%; close > 90%.",
    ]

    return PlaybookMeanReversionSignal(
        symbol=symbol,
        status=status,
        is_triggered=(status == PlaybookSignalStatus.TRIGGERED),
        close_price=last_price,
        sma200=sma200_val,
        sma20=sma20_val,
        sma20_slope=sma20_slope,
        lower_bb=lower_bb,
        upper_bb=upper_bb,
        pct_b=pct_b,
        rsi2=rsi2_val,
        rsi14=rsi14_val,
        atr14=atr14_val,
        day_low=ref_day_low,
        close_above_sma200=close_above_sma200,
        close_below_lower_bb=close_below_lower_bb,
        rsi2_below_10=rsi2_below_10,
        adequate_liquidity=adequate_liquidity,
        risk_limits_pass=risk_limits_passed,
        target_exit_price=target_exit,
        stop_loss_spot_price=stop_loss_spot,
        strategy_name="NIFTY Monthly Bull Put Spread (Playbook v1.4)",
        suggested_structure=actual_trade if actual_trade else "Sell 1x OTM Put (~0.25-0.30 Delta) + Buy 1x OTM Put (Defined Risk Wing 1:1, Never Naked)",
        target_dte_range="30 - 45 DTE Monthly Expiry",
        target_short_delta="~0.30 Absolute Delta (0.15 - 0.25 Delta conservative alternative)",
        exit_rules=exit_rules,
        rationale=rationale,
        high_52w=high_52w,
        dist_52w_pct=dist_52w_pct,
        actual_trade=actual_trade,
        warnings=warnings,
    )


def format_playbook_signal_markdown(signal: PlaybookMeanReversionSignal, iv_analysis: IVRegimeAnalysis | None = None) -> str:
    """Format the Playbook signal evaluation into clean GitHub-flavored Markdown."""
    status_icons = {
        PlaybookSignalStatus.TRIGGERED: "🟢 **ACTIVE TRIGGER**",
        PlaybookSignalStatus.WATCHLIST: "🟡 **WATCHLIST / DIP**",
        PlaybookSignalStatus.STAND_ASIDE: "🔴 **STAND ASIDE / DEFENSIVE**",
        PlaybookSignalStatus.NEUTRAL: "⚪ **NEUTRAL**",
        PlaybookSignalStatus.INELIGIBLE: "⚪ **INELIGIBLE**",
    }
    status_str = status_icons.get(signal.status, str(signal.status))

    ath_info = f" | **52W High**: `{signal.high_52w:,.2f}` (`{signal.dist_52w_pct:+.1f}%`)" if signal.high_52w else ""
    lines = [
        f"### 🛡️ NIFTY Income Portfolio Playbook v1.4 — Mean-Reversion Signal",
        f"- **Instrument**: `{signal.symbol}` | **Last Close**: `{signal.close_price:,.2f}`{ath_info}",
        f"- **Signal Status**: {status_str}",
        "",
        "| Rule / Filter | Indicator Reading | Threshold Requirement | Condition Met? |",
        "| :--- | :--- | :--- | :---: |",
        f"| **1. 200-Day SMA Trend Guardrail** | `{signal.sma200:,.2f}` | Daily Close > 200 SMA | {'✅ Pass' if signal.close_above_sma200 else '❌ Fail (Defensive)'} |",
        f"| **2. Lower Bollinger Band Stretch** | `{signal.lower_bb:,.2f}` (pct_b: `{signal.pct_b:.2f}` if signal.pct_b is not None else 'N/A') | Daily Close < Lower BB (20, 2σ) | {'✅ Pass' if signal.close_below_lower_bb else '❌ No'} |",
        f"| **3. Ultra-Short RSI(2) Crash Filter** | `{signal.rsi2:.1f}` if signal.rsi2 is not None else 'N/A' | RSI(2) < 10.0 | {'✅ Pass' if signal.rsi2_below_10 else '❌ No'} |",
        f"| **4. Liquidity & Contract Specs** | Index F&O Universe | Approved Liquid Index F&O | {'✅ Pass' if signal.adequate_liquidity else '❌ Fail'} |",
        f"| **5. Defined-Risk & Limits Pass** | 1:1 Protective Put Wing | Zero Naked Short Puts | {'✅ Pass' if signal.risk_limits_pass else '❌ Fail'} |",
        "",
        f"> **Signal Diagnosis**: {signal.rationale}",
    ]

    if iv_analysis:
        lines.extend([
            "",
            f"**Playbook IV Regime**: `{iv_analysis.regime.value}` (India VIX: `{iv_analysis.vix:.2f}`, IV Rank: `{iv_analysis.iv_rank:.1f}`)",
            f"- *Recommended Structures*: {', '.join(iv_analysis.recommended_strategies)}",
            f"- *Regime Guidance*: {iv_analysis.guidance}",
        ])

    if signal.is_triggered or signal.status == PlaybookSignalStatus.WATCHLIST:
        lines.extend([
            "",
            "#### 📋 Trade Execution & Management Parameters (Playbook v1.4)",
            f"- **Structure**: `{signal.suggested_structure}`",
            f"- **Target Expiry**: `{signal.target_dte_range}`",
            f"- **Short Delta**: `{signal.target_short_delta}`",
            f"- **Mean-Reversion Target Exit**: Daily close touches 20-day SMA (`~{signal.target_exit_price:,.2f}`)",
            f"- **Spot Stop-Loss Boundary**: Spot closes > 1.5 ATR(14) below entry-day low (`<= {signal.stop_loss_spot_price:,.2f}`)",
            "- **Exit Rules**:",
            *[f"  - {rule}" for rule in signal.exit_rules],
        ])

    return "\n".join(lines)
