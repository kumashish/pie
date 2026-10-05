"""P-Shape Profile indicator (detects price consolidation at upper range following a rally / 2nd leg launch setup)."""

from dataclasses import dataclass
from time import perf_counter

import polars as pl

from pie.market.indicators.base import BaseIndicator, IndicatorResult


@dataclass(frozen=True, slots=True)
class PShapeProfile(BaseIndicator):
    """Calculate P-Shape Price Profile distribution & 2nd-leg breakout score over a lookback window."""

    period: int = 20

    @property
    def name(self) -> str:
        """Return the stable indicator name."""
        return f"P_SHAPE({self.period})"

    def calculate(self, data: pl.DataFrame) -> IndicatorResult:
        """Calculate P-Shape score (0-100), Skew, and breakout confirmation."""
        started_at = perf_counter()
        validation_error = self._validation_error(
            data,
            required_columns=frozenset({"close", "high", "low"}),
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
            recent = data.tail(self.period)
            high_max = float(recent.get_column("high").max())
            low_min = float(recent.get_column("low").min())
            price_range = high_max - low_min

            if price_range <= 0:
                return self._result(
                    value=50.0,
                    valid=True,
                    reason=None,
                    rows=data.height,
                    started_at=started_at,
                    metadata={"period": self.period, "is_p_shape": False, "p_score": 50.0, "skew": 0.0},
                )

            closes = recent.get_column("close")
            # Calculate mean price position within period range [0, 1]
            relative_positions = (closes - low_min) / price_range
            mean_pos = float(relative_positions.mean())

            # Fraction of bars closing in upper 40% of period range (head of the 'P')
            upper_density = float((relative_positions >= 0.60).sum() / self.period)

            # Fraction of bars closing in lower 30% of period range (tail of the 'P')
            lower_density = float((relative_positions <= 0.30).sum() / self.period)

            # P-Shape structure condition: High upper density + Thin lower tail + High mean position
            is_p_shape = (upper_density >= 0.45) and (lower_density <= 0.25) and (mean_pos >= 0.58)

            # 2nd Leg Expansion: Current price near or breaking upper boundary
            last_close = float(closes.last())
            pos_last = (last_close - low_min) / price_range
            breakout_ready = is_p_shape and (pos_last >= 0.80)

            # Overall P-Shape Score (0 to 100)
            p_score = min(100.0, max(0.0, (mean_pos * 40.0) + (upper_density * 40.0) + ((1.0 - lower_density) * 20.0)))

            return self._result(
                value=round(p_score, 2),
                valid=True,
                reason=None,
                rows=data.height,
                started_at=started_at,
                metadata={
                    "period": self.period,
                    "is_p_shape": is_p_shape,
                    "p_score": round(p_score, 2),
                    "upper_density": round(upper_density, 3),
                    "lower_density": round(lower_density, 3),
                    "mean_position": round(mean_pos, 3),
                    "breakout_ready": breakout_ready,
                },
            )
        except (TypeError, ValueError, pl.exceptions.PolarsError):
            return self._result(
                value=None,
                valid=False,
                reason="Unable to calculate P-Shape Profile.",
                rows=data.height,
                started_at=started_at,
                metadata={"period": self.period},
            )
