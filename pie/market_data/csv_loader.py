"""Loading of canonical OHLCV data from local CSV files."""

from pathlib import Path

import polars as pl

REQUIRED_SOURCE_COLUMNS = {"Date", "Open", "High", "Low", "Close", "Volume"}


def load_ohlcv_csv(path: Path) -> pl.DataFrame:
    """Load a Date/Open/High/Low/Close/Volume CSV into canonical OHLCV columns."""
    data = pl.read_csv(path)
    missing_columns = REQUIRED_SOURCE_COLUMNS.difference(data.columns)
    if missing_columns:
        msg = f"CSV is missing required columns: {sorted(missing_columns)}"
        raise ValueError(msg)
    return data.select(
        pl.col("Date").str.strptime(pl.Datetime, format="%Y-%m-%d", strict=True).alias("timestamp"),
        pl.col("Open").cast(pl.Float64, strict=True).alias("open"),
        pl.col("High").cast(pl.Float64, strict=True).alias("high"),
        pl.col("Low").cast(pl.Float64, strict=True).alias("low"),
        pl.col("Close").cast(pl.Float64, strict=True).alias("close"),
        pl.col("Volume").cast(pl.Int64, strict=True).alias("volume"),
    )


def get_symbol_cache_path(symbol: str, storage_dir: Path = Path("data/market")) -> Path:
    """Return canonical CSV file path for a symbol."""
    import re
    safe_symbol = re.sub(r"[^A-Za-z0-9_-]+", "_", symbol).strip("_")
    return storage_dir / f"{safe_symbol}.csv"


def save_market_data(
    symbol: str, new_data: pl.DataFrame, storage_dir: Path = Path("data/market")
) -> pl.DataFrame:
    """Save and incrementally append OHLCV market data for a stock, deduplicating by timestamp.

    Returns the complete, updated DataFrame.
    """
    storage_dir.mkdir(parents=True, exist_ok=True)
    file_path = get_symbol_cache_path(symbol, storage_dir)

    combined = new_data
    if file_path.exists():
        try:
            existing_data = pl.read_csv(file_path)
            if existing_data.schema["timestamp"] == pl.Utf8:
                existing_data = existing_data.with_columns(
                    pl.col("timestamp").str.strptime(pl.Datetime, strict=False)
                )
            combined = pl.concat([existing_data, new_data], how="vertical_relaxed")
        except Exception:
            combined = new_data

    combined = (
        combined.drop_nulls(subset=["open", "high", "low", "close"])
        .filter(
            (pl.col("open") > 0)
            & (pl.col("high") > 0)
            & (pl.col("low") > 0)
            & (pl.col("close") > 0)
        )
        .unique(subset=["timestamp"], keep="last")
        .sort("timestamp")
    )
    formatted_data = combined.with_columns(
        pl.col("timestamp").dt.strftime("%Y-%m-%d %H:%M:%S").alias("timestamp")
    )
    formatted_data.write_csv(file_path)
    return combined


def load_cached_market_data(
    symbol: str, storage_dir: Path = Path("data/market")
) -> pl.DataFrame | None:
    """Load cached local OHLCV market data for a stock if available."""
    file_path = get_symbol_cache_path(symbol, storage_dir)
    if not file_path.exists():
        return None
    try:
        data = pl.read_csv(file_path)
        if data.schema["timestamp"] == pl.Utf8:
            data = data.with_columns(
                pl.col("timestamp").str.strptime(pl.Datetime, strict=False)
            )
        clean_data = (
            data.drop_nulls(subset=["open", "high", "low", "close"])
            .filter(
                (pl.col("open") > 0)
                & (pl.col("high") > 0)
                & (pl.col("low") > 0)
                & (pl.col("close") > 0)
            )
            .sort("timestamp")
        )
        return clean_data if clean_data.height > 0 else None
    except Exception:
        return None
