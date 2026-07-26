"""Independent rules used by the quantitative trend engine."""

from collections.abc import Mapping
from dataclasses import dataclass

import polars as pl

from pie.core.models import MarketSnapshot
from pie.market.indicators.base import IndicatorResult


@dataclass(frozen=True, slots=True)
class RuleResult:
    """Result of evaluating one weighted trend rule."""

    name: str
    passed: bool
    evaluated: bool
    weight: float
    explanation: str


class TrendRule:
    """Base contract for independent trend rules."""

    name: str
    weight: float

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Evaluate this rule without interpreting any other rule's outcome."""
        raise NotImplementedError

    def _indicator(self, indicators: Mapping[str, IndicatorResult], name: str) -> float | None:
        result = indicators.get(name)
        if result is None or not result.valid or not result.warmup_complete:
            return None
        return result.value

    def _unavailable(self, explanation: str) -> RuleResult:
        return RuleResult(self.name, False, False, self.weight, explanation)


@dataclass(frozen=True, slots=True)
class PriceAboveEMA200Rule(TrendRule):
    name: str = "Price above EMA200"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check whether the last price is above EMA200."""
        ema200 = self._indicator(indicators, "EMA200")
        if ema200 is None:
            return self._unavailable("EMA200 is unavailable.")
        passed = float(snapshot.last_price) > ema200
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "Price is above EMA200." if passed else "Price is below EMA200.",
        )


@dataclass(frozen=True, slots=True)
class EMA20AboveEMA50Rule(TrendRule):
    name: str = "EMA20 above EMA50"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check the short-term EMA crossover."""
        ema20 = self._indicator(indicators, "EMA20")
        ema50 = self._indicator(indicators, "EMA50")
        if ema20 is None or ema50 is None:
            return self._unavailable("EMA20 or EMA50 is unavailable.")
        passed = ema20 > ema50
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "EMA20 is above EMA50." if passed else "EMA20 is not above EMA50.",
        )


@dataclass(frozen=True, slots=True)
class EMA50AboveEMA200Rule(TrendRule):
    name: str = "EMA50 above EMA200"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check the long-term EMA stack."""
        ema50 = self._indicator(indicators, "EMA50")
        ema200 = self._indicator(indicators, "EMA200")
        if ema50 is None or ema200 is None:
            return self._unavailable("EMA50 or EMA200 is unavailable.")
        passed = ema50 > ema200
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "EMA50 is above EMA200." if passed else "EMA50 is not above EMA200.",
        )


@dataclass(frozen=True, slots=True)
class RSIHealthyRule(TrendRule):
    name: str = "RSI between 50 and 65"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check whether RSI is in a healthy trend range."""
        rsi = self._indicator(indicators, "RSI(14)")
        if rsi is None:
            return self._unavailable("RSI(14) is unavailable.")
        passed = 50.0 <= rsi <= 65.0
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "RSI is healthy." if passed else "RSI is outside the healthy range.",
        )


@dataclass(frozen=True, slots=True)
class ADXStrongRule(TrendRule):
    name: str = "ADX above 30"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check whether trend strength exceeds the ADX threshold."""
        adx = self._indicator(indicators, "ADX(14)")
        if adx is None:
            return self._unavailable("ADX(14) is unavailable.")
        passed = adx > 30.0
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "ADX indicates a strong trend." if passed else "ADX does not indicate a strong trend.",
        )


@dataclass(frozen=True, slots=True)
class ATRIncreasingRule(TrendRule):
    name: str = "ATR increasing"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check whether the 14-period true range is expanding."""
        required_columns = {"high", "low", "close"}
        if history.height < 16 or not required_columns.issubset(history.columns):
            return self._unavailable("Insufficient history for ATR expansion.")
        previous_close = pl.col("close").shift(1).fill_null(pl.col("close"))
        true_range = pl.max_horizontal(
            pl.col("high") - pl.col("low"),
            (pl.col("high") - previous_close).abs(),
            (pl.col("low") - previous_close).abs(),
        )
        values = (
            history.select(true_range.rolling_mean(window_size=14))
            .drop_nulls()
            .tail(2)
            .to_series()
            .to_list()
        )
        if len(values) < 2:
            return self._unavailable("Insufficient history for ATR expansion.")
        passed = float(values[-1]) > float(values[-2])
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "ATR is expanding." if passed else "ATR is not expanding.",
        )


@dataclass(frozen=True, slots=True)
class HigherHighsRule(TrendRule):
    name: str = "Price making higher highs"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check whether the latest high exceeds the previous high."""
        if history.height < 2 or "high" not in history.columns:
            return self._unavailable("Insufficient history for higher highs.")
        highs = history.get_column("high").tail(2).to_list()
        passed = float(highs[-1]) > float(highs[-2])
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "Price is making higher highs." if passed else "Price is not making higher highs.",
        )


@dataclass(frozen=True, slots=True)
class HigherLowsRule(TrendRule):
    name: str = "Price making higher lows"
    weight: float = 0.0

    def evaluate(
        self,
        snapshot: MarketSnapshot,
        indicators: Mapping[str, IndicatorResult],
        history: pl.DataFrame,
    ) -> RuleResult:
        """Check whether the latest low exceeds the previous low."""
        if history.height < 2 or "low" not in history.columns:
            return self._unavailable("Insufficient history for higher lows.")
        lows = history.get_column("low").tail(2).to_list()
        passed = float(lows[-1]) > float(lows[-2])
        return RuleResult(
            self.name,
            passed,
            True,
            self.weight,
            "Price is making higher lows." if passed else "Price is not making higher lows.",
        )
