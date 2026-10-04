"""Realized Volatility / VIX technical indicator implementation."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult
from pie.market.vix import calculate_realized_vix


@dataclass(frozen=True, slots=True)
class RealizedVIX(BaseIndicator):
    """Calculate rolling annualized realized volatility (VIX proxy) indicator."""

    window: int = 30
    annualization_factor: float = 252.0

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"RealizedVIX({self.window})"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate the latest realized VIX value."""
        started_at = perf_counter()
        validation_error = self._validation_error(
            data,
            required_columns=frozenset({"close"}),
            minimum_history=self.window + 1,
        )
        if validation_error:
            return self._result(
                value=None,
                valid=False,
                reason=validation_error,
                rows=data.height,
                started_at=started_at,
                metadata={"window": self.window},
            )

        try:
            vix_val = calculate_realized_vix(
                data,
                window=self.window,
                annualization_factor=self.annualization_factor,
            )
            if vix_val is None:
                return self._result(
                    value=None,
                    valid=False,
                    reason="Insufficient valid price data for VIX calculation.",
                    rows=data.height,
                    started_at=started_at,
                    metadata={"window": self.window},
                )
            return self._result(
                value=vix_val,
                valid=True,
                reason=None,
                rows=data.height,
                started_at=started_at,
                metadata={"window": self.window, "annualization_factor": self.annualization_factor},
            )
        except Exception as exc:
            return self._result(
                value=None,
                valid=False,
                reason=f"Unable to calculate VIX: {exc}",
                rows=data.height,
                started_at=started_at,
                metadata={"window": self.window},
            )
