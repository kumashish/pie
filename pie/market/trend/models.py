"""Immutable domain models for quantitative trend analysis."""

from datetime import datetime
from enum import StrEnum

from pydantic import Field

from pie.core.models import DomainModel


class MarketRegime(StrEnum):
    """Discrete classification of a quantitative trend score."""

    UNKNOWN = "unknown"
    STRONG_BULL = "strong_bull"
    BULL = "bull"
    NEUTRAL = "neutral"
    BEAR = "bear"
    STRONG_BEAR = "strong_bear"


class ConfidenceGrade(StrEnum):
    """Letter grade derived from numerical confidence score."""

    GRADE_A = "A (High Conviction)"
    GRADE_B = "B (Moderate Conviction)"
    GRADE_C = "C (Low Conviction)"
    GRADE_F = "F (Untrusted)"


class TrendScore(DomainModel):
    """A normalized trend score ranging from zero to ten."""

    value: float = Field(ge=0.0, le=10.0)


class ConfidenceScore(DomainModel):
    """Confidence in the completeness of a trend analysis."""

    value: float = Field(ge=0.0, le=1.0)

    @property
    def grade(self) -> ConfidenceGrade:
        """Return a letter grade for the confidence score."""
        if self.value >= 0.90:
            return ConfidenceGrade.GRADE_A
        if self.value >= 0.75:
            return ConfidenceGrade.GRADE_B
        if self.value >= 0.50:
            return ConfidenceGrade.GRADE_C
        return ConfidenceGrade.GRADE_F


class TrendAnalysis(DomainModel):
    """Deterministic market-trend assessment without trade recommendations."""

    symbol: str = Field(min_length=1)
    timestamp: datetime
    trend_score: TrendScore
    confidence: ConfidenceScore
    regime: MarketRegime
    explanation: str = Field(min_length=1)
    indicator_values: dict[str, float | None]
    passed_rules: tuple[str, ...] = ()
    failed_rules: tuple[str, ...] = ()
