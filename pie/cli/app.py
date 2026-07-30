"""Typer command-line interface."""

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated

import polars as pl
import typer
from rich.console import Console
from rich.table import Table

from pie.cli.readme import readme_app
from pie.config.loader import load_config
from pie.config.models import TrendWeights
from pie.core.signal_state import SignalStateManager
from pie.market.backtest.engine import TrendBacktester
from pie.market.indicators.engine import IndicatorEngine
from pie.market.strategy import StrategyRecommendation, select_strategy
from pie.market.trade_estimate import EstimatedTrade, estimate_trade
from pie.market.trend.engine import TrendEngine
from pie.market_data.csv_loader import load_cached_market_data, load_ohlcv_csv, save_market_data
from pie.market_data.exceptions import MarketDataError
from pie.market_data.snapshots import SnapshotBuilder
from pie.providers.yahoo import UrllibHTTPClient, YahooFinanceProvider
from pie.reporting.market import write_market_report
from pie.reporting.snapshot import upsert_snapshot_entry

from pie.market.exit_rules import evaluate_exit_condition
from pie.reporting.notifications import NotificationDispatcher

app = typer.Typer(help="Portfolio Intelligence Engine.", no_args_is_help=True)
app.add_typer(readme_app, name="readme")
console = Console()

MARKET_NAMES = {
    "^NSEI": "NIFTY 50",
    "^NSEBANK": "BANKNIFTY",
    "NIFTY_FIN_SERVICE.NS": "FINNIFTY",
    "^NSEMDCP50": "MIDCAPNIFTY",
    "^BSESN": "SENSEX",
    "SPY": "SPY",
    "QQQ": "QQQ",
}
OPTION_SYMBOL_NAMES = {
    "^NSEI": "NIFTY",
    "^NSEBANK": "BANKNIFTY",
    "NIFTY_FIN_SERVICE.NS": "FINNIFTY",
    "^NSEMDCP50": "MIDCAPNIFTY",
    "^BSESN": "SENSEX",
    "SPY": "SPY",
    "QQQ": "QQQ",
}
REGIME_LABELS = {
    "strong_bull": "🟢 Strong Bull",
    "bull": "🟢 Bull",
    "neutral": "🟡 Neutral",
    "bear": "🔴 Bear",
    "strong_bear": "🔴 Strong Bear",
    "unknown": "⚪ Unknown",
}

VIX_SYMBOLS = {
    "^NSEI": "^INDIAVIX",
    "^NSEBANK": "^INDIAVIX",
    "NIFTY_FIN_SERVICE.NS": "^INDIAVIX",
    "^NSEMDCP50": "^INDIAVIX",
    "^BSESN": "^INDIAVIX",
    "SPY": "^VIX",
    "QQQ": "^VIX",
}
FALLBACK_VIX = {
    "^NSEI": 15.0,
    "^NSEBANK": 15.0,
    "NIFTY_FIN_SERVICE.NS": 15.0,
    "^NSEMDCP50": 15.0,
    "^BSESN": 15.0,
    "SPY": 20.0,
    "QQQ": 20.0,
}


def _format_strike(strike: float) -> str:
    return str(int(strike)) if strike == int(strike) else str(strike)


def format_trade_legs(symbol: str, estimated_trade: EstimatedTrade | None) -> str:
    """Render an estimated trade as option-symbol-style leg lines.

    e.g. "Buy 1x NIFTY 28-Jul-2026 23600 Put<br> Sell 1x NIFTY 28-Jul-2026 23000 Put"
    or Butterfly: "Buy 1x HINDALCO 25-Aug-2026 920 Call<br> Sell 2x HINDALCO 25-Aug-2026 940 Call<br> Buy 1x HINDALCO 25-Aug-2026 970 Call"
    """
    if estimated_trade is None:
        return "No Trade"
    display_symbol = OPTION_SYMBOL_NAMES.get(symbol, symbol)
    clean_symbol = display_symbol.replace(".NS", "").replace(".ns", "").strip()
    expiry = estimated_trade.expiration.strftime("%d-%b-%Y")
    right_suffix = {"put": "Put", "call": "Call"}

    grouped: list[tuple[TradeLeg, int]] = []
    for leg in estimated_trade.legs:
        if (
            grouped
            and grouped[-1][0].action == leg.action
            and grouped[-1][0].right == leg.right
            and grouped[-1][0].strike == leg.strike
        ):
            prev_leg, count = grouped[-1]
            grouped[-1] = (prev_leg, count + 1)
        else:
            grouped.append((leg, 1))

    lines = []
    for leg, count in grouped:
        strike_str = _format_strike(leg.strike)
        right_str = right_suffix[leg.right.value]
        qty_str = f" {count}x" if count > 1 else ""
        lines.append(f"{leg.action.title()}{qty_str} {clean_symbol} {expiry} {strike_str} {right_str}")

    return "<br> ".join(lines)



@app.command("analyze-market")
def analyze_market(
    symbol: str,
    config: Annotated[
        Path | None, typer.Option(help="Optional YAML indicator configuration.")
    ] = None,
    output_dir: Annotated[
        Path, typer.Option(help="Directory for the timestamped text analysis report.")
    ] = Path("reports/market"),
) -> None:
    """Fetch market data, persist/append to local CSV cache, and calculate indicators."""
    try:
        fetched_data = YahooFinanceProvider(UrllibHTTPClient()).fetch_history(
            symbol,
            period="2y",
            interval="1d",
        )
        data = save_market_data(symbol, fetched_data)
    except MarketDataError as error:
        cached_data = load_cached_market_data(symbol)
        if cached_data is not None and cached_data.height >= 200:
            console.print(
                f"[yellow]Live fetch unavailable for {symbol}. Reusing local cached data ({cached_data.height} rows).[/yellow]"
            )
            data = cached_data
        else:
            console.print(f"Unable to analyze {symbol}: {error}", style="red")
            raise typer.Exit(code=1) from error
    application_config = load_config(config) if config is not None else None
    configurations = application_config.indicators if application_config is not None else []
    engine = (
        IndicatorEngine.from_config(configurations) if configurations else IndicatorEngine.default()
    )
    results = engine.calculate(data)
    snapshots = SnapshotBuilder().build(symbol, data)
    snapshot = snapshots[-1]
    trend = TrendEngine.from_weights(
        application_config.trend.weights.as_mapping()
        if application_config is not None
        else TrendWeights().as_mapping()
    ).analyze(snapshot, results, data)
    vix, vix_source = _fetch_vix(symbol)
    iv_rank = _calculate_iv_rank(data, vix)
    recommendation = select_strategy(trend, iv_rank=iv_rank)
    estimated_trade = estimate_trade(symbol, float(snapshot.last_price), vix, recommendation, vix_source)
    report_path = write_market_report(
        output_dir,
        snapshot,
        results,
        trend,
        recommendation,
        estimated_trade,
    )
    generated_at = datetime.now(UTC)
    prev_state = SignalStateManager().load_state(symbol)
    prev_regime = prev_state.last_regime if prev_state else trend.regime.value
    prev_strategy = prev_state.last_strategy if prev_state else recommendation.strategy.value

    state, status = SignalStateManager().update_state(
        symbol=symbol,
        strategy=recommendation.strategy.value,
        regime=trend.regime.value,
    )

    # Evaluate quantitative exit rules for active trade
    should_exit = False
    exit_reason = ""
    if estimated_trade is not None:
        should_exit, exit_reason = evaluate_exit_condition(
            symbol=symbol,
            spot_price=float(snapshot.last_price),
            expiration=estimated_trade.expiration.isoformat(),
            current_regime=trend.regime.value,
            current_score=trend.trend_score.value,
            previous_regime=prev_regime,
            previous_strategy=prev_strategy,
            estimated_trade=estimated_trade,
            current_time=generated_at,
        )

    if should_exit:
        signal_label = exit_reason
    elif not recommendation.actionable:
        signal_label = "Hold"
    elif status in {"NEW", "CHANGED"}:
        signal_label = "New"
    else:
        signal_label = "Active"

    best_score = float(recommendation.fit_scores.get(recommendation.strategy.value, 0.0))
    market_row = {
        "symbol": symbol,
        "market": MARKET_NAMES.get(symbol, symbol),
        "last_updated": generated_at.isoformat(),
        "trend": REGIME_LABELS.get(trend.regime.value, trend.regime.value),
        "strategy": format_trade_legs(symbol, estimated_trade),
        "strategy_type": recommendation.strategy.value,
        "fit_score": best_score,
        "signal": signal_label,
        "signal_since": state.trend_started_at.isoformat(),
    }
    upsert_snapshot_entry(Path("reports/market/snapshot.json"), market_row)

    # Dispatch real-time Telegram alert if signal is NEW or an EXIT/REVIEW trigger
    if signal_label == "New" or should_exit:
        NotificationDispatcher().dispatch_high_conviction_alert(market_row)
    table = Table(title=f"Market Snapshot: {symbol}")
    table.add_column("Indicator")
    table.add_column("Value", justify="right")
    table.add_row("Last Price", f"{float(snapshot.last_price):,.2f}")
    for result in results.values():
        value = f"{result.value:,.2f}" if result.valid and result.value is not None else "N/A"
        table.add_row(result.name, value)
    console.print(table)
    console.print(f"Market Regime: {trend.regime.replace('_', ' ').title()}")
    console.print(f"Trend Score: {trend.trend_score.value:.1f}")
    console.print(f"Confidence: {trend.confidence.value:.0%} [Grade: {trend.confidence.grade}]")
    console.print(trend.explanation)
    console.print(f"Recommendation: {recommendation.strategy.replace('_', ' ').title()}")
    if estimated_trade is not None:
        console.print(f"Suggested expiry: {estimated_trade.expiration.isoformat()}")
    console.print(f"Report saved: {report_path}")


@app.command("backtest-market")
def backtest_market(
    symbol: str,
    config: Annotated[
        Path | None, typer.Option(help="Optional YAML indicator and trend configuration.")
    ] = None,
    data_path: Annotated[
        Path | None, typer.Option(help="Optional local Date/Open/High/Low/Close/Volume CSV file.")
    ] = None,
) -> None:
    """Backtest directional trend signals against historical index returns."""
    if data_path is not None:
        data = load_ohlcv_csv(data_path)
    else:
        try:
            data = YahooFinanceProvider(UrllibHTTPClient()).fetch_history(
                symbol,
                period="5y",
                interval="1d",
            )
        except MarketDataError as error:
            console.print(f"Unable to backtest {symbol}: {error}", style="red")
            raise typer.Exit(code=1) from error
    application_config = load_config(config) if config is not None else None
    configurations = application_config.indicators if application_config is not None else []
    indicator_engine = (
        IndicatorEngine.from_config(configurations) if configurations else IndicatorEngine.default()
    )
    weights = (
        application_config.trend.weights.as_mapping()
        if application_config is not None
        else TrendWeights().as_mapping()
    )
    report = TrendBacktester(indicator_engine, TrendEngine.from_weights(weights)).run(symbol, data)
    table = Table(title=f"Trend Signal Backtest: {symbol}")
    table.add_column("Metric")
    table.add_column("Value", justify="right")
    table.add_row("Closed signals", str(len(report.trades)))
    table.add_row("Win rate", f"{report.win_rate:.1%}")
    table.add_row("Average move", f"{report.average_return_percent:.2f}%")
    table.add_row("Cumulative return", f"{report.cumulative_return_percent:.2f}%")
    table.add_row("Maximum drawdown", f"{report.maximum_drawdown_percent:.2f}%")
    console.print(table)
    for assumption in report.assumptions:
        console.print(f"- {assumption}")


@app.command()
def portfolio(account_id: str) -> None:
    """Placeholder command for inspecting a portfolio."""
    console.print(f"Portfolio inspection for {account_id} is not implemented yet.")


@app.command()
def recommend(account_id: str) -> None:
    """Placeholder command for producing a recommendation."""
    console.print(f"Recommendation generation for {account_id} is not implemented yet.")


@app.command("config-check")
def config_check(path: Path) -> None:
    """Validate a configuration file."""
    load_config(path)
    console.print(f"Configuration is valid: {path}")


@app.command("serve")
def serve(
    port: int = typer.Option(8090, "--port", "-p", help="Port to run the web UI server on."),
    open_browser: bool = typer.Option(True, "--open/--no-open", help="Open browser automatically."),
) -> None:
    """Launch the interactive web UI dashboard server."""
    import webbrowser
    from pie.web.server import start_web_server

    url = f"http://localhost:{port}"
    console.print(f"[bold green]Starting Portfolio Intelligence Web Engine at {url}[/bold green]")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    start_web_server(port=port)


def main() -> None:
    """Run the CLI application."""
    app()


def _calculate_iv_rank(data: pl.DataFrame, vix: float) -> float:
    """Calculate stock volatility rank from rolling Historical Volatility (HV) percentile combined with VIX."""
    vix_rank = min(100.0, max(0.0, ((vix - 12.0) / (30.0 - 12.0)) * 100.0))
    if "close" not in data.columns or data.height < 30:
        return vix_rank
    try:
        close = data.get_column("close")
        returns = (close / close.shift(1)).log()
        hv20 = (returns.rolling_std(window_size=20) * (252.0 ** 0.5)).drop_nulls()
        if hv20.is_empty():
            return vix_rank
        current_hv = float(hv20.tail(1).item())
        min_hv = float(hv20.min())
        max_hv = float(hv20.max())
        hv_rank = min(100.0, max(0.0, ((current_hv - min_hv) / (max_hv - min_hv + 1e-6)) * 100.0))
        return round(hv_rank * 0.65 + vix_rank * 0.35, 1)
    except Exception:
        return vix_rank


def _fetch_vix(symbol: str) -> tuple[float, str]:
    """Fetch live VIX value or fallback assumption for a given symbol."""
    vix_symbol = VIX_SYMBOLS.get(symbol, "^VIX")
    try:
        vix_data = YahooFinanceProvider(UrllibHTTPClient()).fetch_history(
            vix_symbol,
            period="5d",
            interval="1d",
        )
        vix = float(vix_data.get_column("close").tail(1).item())
        return vix, f"live {vix_symbol}"
    except (IndexError, MarketDataError, TypeError, ValueError):
        return FALLBACK_VIX.get(symbol, 20.0), "fallback assumption"


def _estimate_trade(
    symbol: str, spot_price: Decimal, recommendation: StrategyRecommendation
) -> EstimatedTrade | None:
    if not recommendation.actionable:
        return None
    vix, vix_source = _fetch_vix(symbol)
    return estimate_trade(symbol, float(spot_price), vix, recommendation, vix_source)
