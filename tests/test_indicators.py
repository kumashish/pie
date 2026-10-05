import math

import polars as pl
import pytest

from pie.market.indicators import ADX, ATR, EMA, RSI, IndicatorEngine
from pie.market.indicators.p_shape import PShapeProfile


def ohlcv(rows: int = 30, *, close_values: list[float] | None = None) -> pl.DataFrame:
    closes = close_values or [100.0 + index for index in range(rows)]
    return pl.DataFrame(
        {
            "timestamp": list(range(len(closes))),
            "open": closes,
            "high": [value + 1.0 for value in closes],
            "low": [value - 1.0 for value in closes],
            "close": closes,
            "volume": [1_000] * len(closes),
        }
    )


def test_ema_calculates_constant_price() -> None:
    result = EMA(3).calculate(ohlcv(close_values=[100.0, 100.0, 100.0]))

    assert result.valid is True
    assert result.value == 100.0


def test_rsi_handles_constant_prices_without_division_by_zero() -> None:
    result = RSI(3).calculate(ohlcv(close_values=[100.0] * 4))

    assert result.valid is True
    assert result.value == 50.0


def test_rsi_returns_hundred_for_only_gains() -> None:
    result = RSI(3).calculate(ohlcv(close_values=[100.0, 101.0, 102.0, 103.0]))

    assert result.valid is True
    assert result.value == 100.0


def test_atr_calculates_known_constant_range() -> None:
    result = ATR(3).calculate(ohlcv(close_values=[100.0] * 4))

    assert result.valid is True
    assert result.value == 2.0


def test_adx_handles_constant_prices_without_division_by_zero() -> None:
    result = ADX(3).calculate(ohlcv(close_values=[100.0] * 5))

    assert result.valid is True
    assert result.value == 0.0


def test_p_shape_profile_detects_upper_consolidation() -> None:
    # 5 initial low tail bars, followed by 15 upper consolidation bars
    closes = [100.0, 101.0, 102.0, 103.0, 104.0] + [118.0, 119.0, 120.0] * 5
    df = pl.DataFrame(
        {
            "open": closes,
            "high": [c + 0.5 for c in closes],
            "low": [c - 0.5 for c in closes],
            "close": closes,
        }
    )
    result = PShapeProfile(20).calculate(df)
    assert result.valid is True
    assert result.metadata["is_p_shape"] is True
    assert result.metadata["p_score"] > 60.0


@pytest.mark.parametrize(
    "data", [pl.DataFrame(), ohlcv(rows=2), ohlcv().with_columns(pl.lit(None).alias("close"))]
)
def test_indicators_return_invalid_results_for_invalid_data(data: pl.DataFrame) -> None:
    result = EMA(3).calculate(data)

    assert result.valid is False
    assert result.value is None
    assert result.reason is not None


def test_engine_calculates_configured_indicators() -> None:
    engine = IndicatorEngine.from_config([{"ema": {"period": 3}}, {"rsi": {"period": 3}}, {"p_shape": {"period": 5}}])

    results = engine.calculate(ohlcv())

    assert set(results) == {"EMA3", "RSI(3)", "P_SHAPE(5)"}
    assert all(result.valid for result in results.values())
    assert math.isfinite(results["EMA3"].value or 0.0)


def test_engine_rejects_unknown_indicator_configuration() -> None:
    with pytest.raises(ValueError, match="Unsupported indicator"):
        IndicatorEngine.from_config([{"macd": {"period": 12}}])
