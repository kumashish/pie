"""Simple moving average indicator for trend and mean-reversion analysis."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult


@dataclass(frozen=True, slots=True)
class SMA(BaseIndicator):
    """Calculate a simple moving average and slope of closing prices."""

    period: int

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"SMA{self.period}"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the latest SMA value and slope."""
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
                metadata={"period": self.period},
            )
        try:
            rolling_series = data.select(
                pl.col("close").rolling_mean(window_size=self.period).alias("sma")
            ).get_column("sma")

            latest_val = rolling_series.tail(1).item()
            if latest_val is None:
                return self._result(
                    value=None,
                    valid=False,
                    reason="SMA warmup incomplete.",
                    rows=data.height,
                    started_at=started_at,
                    metadata={"period": self.period},
                )

            # Calculate 5-day slope percentage if history allows
            slope_5d = 0.0
            if rolling_series.len() >= 6:
                prev_val = rolling_series.slice(-6, 1).item()
                if prev_val is not None and prev_val > 0:
                    slope_5d = round(((float(latest_val) - float(prev_val)) / float(prev_val)) * 100.0, 3)

            return self._result(
                value=round(float(latest_val), 2),
                valid=True,
                reason=None,
                rows=data.height,
                started_at=started_at,
                metadata={
                    "period": self.period,
                    "sma": round(float(latest_val), 2),
                    "slope_5d": slope_5d,
                },
            )
        except (TypeError, ValueError, pl.exceptions.PolarsError):
            return self._result(
                value=None,
                valid=False,
                reason="Unable to calculate SMA.",
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
