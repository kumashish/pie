"""Bollinger Bands indicator for volatility and mean-reversion analysis."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult


@dataclass(frozen=True, slots=True)
class BollingerBands(BaseIndicator):
    """Calculate 20-period 2-standard-deviation Bollinger Bands (%B and Bandwidth)."""

    period: int = 20
    num_std: float = 2.0

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"BB({self.period},{int(self.num_std) if self.num_std.is_integer() else self.num_std})"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the latest Bollinger %B and Bandwidth."""
        started_at = perf_counter()
        validation_error = self._validation_error(
            data,
            required_columns=frozenset({"close"}),
            minimum_history=self.period,
        )
        if validation_error:
            return self._result(
                value=None,
                valid=False,
                reason=validation_error,
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period, "num_std": self.num_std},
            )
        try:
            df = data.select(
                pl.col("close"),
                pl.col("close").rolling_mean(window_size=self.period).alias("sma"),
                pl.col("close").rolling_std(window_size=self.period).alias("std"),
            ).with_columns(
                (pl.col("sma") + pl.col("std") * self.num_std).alias("upper"),
                (pl.col("sma") - pl.col("std") * self.num_std).alias("lower"),
            ).with_columns(
                ((pl.col("upper") - pl.col("lower")) / pl.col("sma")).alias("bandwidth"),
                (
                    pl.when((pl.col("upper") - pl.col("lower")) == 0)
                    .then(0.5)
                    .otherwise((pl.col("close") - pl.col("lower")) / (pl.col("upper") - pl.col("lower")))
                ).alias("pct_b"),
            )

            latest = df.tail(1)
            pct_b_val = float(latest.get_column("pct_b").item())
            bandwidth_val = float(latest.get_column("bandwidth").item())
            upper_val = float(latest.get_column("upper").item())
            lower_val = float(latest.get_column("lower").item())
            sma_val = float(latest.get_column("sma").item())

            return self._result(
                value=round(pct_b_val, 4),
                valid=True,
                reason=None,
                rows=data.height,
                started_at=started_at,
                metadata={
                    "period": self.period,
                    "num_std": self.num_std,
                    "pct_b": round(pct_b_val, 4),
                    "bandwidth": round(bandwidth_val, 4),
                    "upper": round(upper_val, 2),
                    "lower": round(lower_val, 2),
                    "middle": round(sma_val, 2),
                },
            )
        except (TypeError, ValueError, pl.exceptions.PolarsError):
            return self._result(
                value=None,
                valid=False,
                reason="Unable to calculate Bollinger Bands.",
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period, "num_std": self.num_std},
            )
