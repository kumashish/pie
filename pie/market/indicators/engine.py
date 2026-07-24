"""Configurable orchestration for independent technical indicators."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import polars as pl

from pie.market.indicators.adx import ADX
from pie.market.indicators.atr import ATR
from pie.market.indicators.base import Indicator, IndicatorResult
from pie.market.indicators.bollinger import BollingerBands
from pie.market.indicators.ema import EMA
from pie.market.indicators.rsi import RSI

DEFAULT_INDICATORS: tuple[Indicator, ...] = (
    EMA(20),
    EMA(50),
    EMA(100),
    EMA(200),
    RSI(14),
    ATR(14),
    ADX(14),
    BollingerBands(20, 2.0),
)


@dataclass(frozen=True, slots=True)
class IndicatorEngine:
    """Calculate a configured collection of independent indicators."""

    indicators: Sequence[Indicator]

    def calculate(self, data: pl.DataFrame) -> dict[str, IndicatorResult]:
        """Calculate every configured indicator against the same OHLCV data."""
        return {indicator.name: indicator.calculate(data) for indicator in self.indicators}

    @classmethod
    def default(cls) -> "IndicatorEngine":
        """Build the default market-analysis indicator set."""
        return cls(indicators=DEFAULT_INDICATORS)

    @classmethod
    def from_config(
        cls, configurations: Sequence[Mapping[str, Mapping[str, object]]]
    ) -> "IndicatorEngine":
        """Build indicators from YAML-compatible indicator configuration."""
        indicators: list[Indicator] = []
        for configuration in configurations:
            if len(configuration) != 1:
                msg = "Each indicator configuration must contain exactly one indicator."
                raise ValueError(msg)
            indicator_type, options = next(iter(configuration.items()))
            period = options.get("period")
            if not isinstance(period, int) or isinstance(period, bool) or period <= 0:
                msg = f"Indicator '{indicator_type}' requires a positive integer period."
                raise ValueError(msg)
            match indicator_type:
                case "ema":
                    indicators.append(EMA(period))
                case "rsi":
                    indicators.append(RSI(period))
                case "atr":
                    indicators.append(ATR(period))
                case "adx":
                    indicators.append(ADX(period))
                case "bollinger":
                    indicators.append(BollingerBands(period))
                case _:
                    msg = f"Unsupported indicator '{indicator_type}'."
                    raise ValueError(msg)
        return cls(indicators=tuple(indicators))
