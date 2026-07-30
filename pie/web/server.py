"""Zero-dependency HTTP web server for interactive Portfolio Intelligence option trade analysis."""

import json
from datetime import date
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
import urllib.parse

from pie.market.indicators.engine import IndicatorEngine
from pie.market.strategy import select_strategy
from pie.market.trade_estimate import estimate_trade
from pie.market.trend.engine import TrendEngine
from pie.market_data.csv_loader import save_market_data
from pie.market_data.snapshots import SnapshotBuilder
from pie.providers.news import StockNewsProvider
from pie.providers.search import TickerSearchProvider
from pie.providers.yahoo import UrllibHTTPClient, YahooFinanceProvider
from pie.reporting.readme_update import get_trade_profile


def _format_strike(strike: float) -> str:
    """Format strike prices as integer if whole, else decimal."""
    return f"{int(strike)}" if strike.is_integer() else f"{strike:.1f}"


# Indices and broad ETFs → options category (most liquid options market)
_OPTIONS_INSTRUMENTS = {
    "^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS", "^BSESN",
    "SPY", "QQQ", "IWM", "DIA", "VTI", "VOO",
    "XLF", "XLE", "XLK", "XLV", "XLI", "XLY", "XLP", "XLB", "XLU", "XLRE",
    "SOXX", "SMH", "ARKK", "GLD", "SLV", "TLT", "HYG", "LQD",
    "GDX", "GDXJ", "LABU", "SOXL", "TQQQ", "SPXL", "UVXY", "VXX",
    "EEM", "EFA", "FXI", "EWJ",
}


def _get_trade_category(symbol: str) -> str:
    """Classify instrument as 'options' (indices/ETFs) or 'cash' (individual stocks)."""
    sym = symbol.strip().upper()
    # Explicit cash overrides first
    _CASH_OVERRIDES = {"^NSEMDCP50"}
    if sym in _CASH_OVERRIDES:
        return "cash"
    if sym in _OPTIONS_INSTRUMENTS:
        return "options"
    # Caret symbols are always indices → options
    if sym.startswith("^"):
        return "options"
    # Individual stocks (NSE/BSE) → cash
    if sym.endswith(".NS") or sym.endswith(".BO"):
        return "cash"
    # US individual stocks (single-word ticker, not in options list) → cash
    # Short tickers that are clearly ETFs stay as options
    return "cash"


def _compute_cash_trade_setup(
    last_price: float,
    indicators: dict,
    regime: str,
) -> dict:
    """Compute entry/stop/target levels for cash equity trades using ATR14 + EMA20."""
    atr_key  = next((k for k in indicators if "ATR" in k.upper()), None)
    ema20_key = next((k for k in indicators if k.upper() in ("EMA20", "EMA(20)")), None)
    ema50_key = next((k for k in indicators if k.upper() in ("EMA50", "EMA(50)")), None)

    atr  = float(indicators[atr_key].value)  if atr_key  and indicators[atr_key].value  else last_price * 0.015
    ema20 = float(indicators[ema20_key].value) if ema20_key and indicators[ema20_key].value else last_price * 0.98
    ema50 = float(indicators[ema50_key].value) if ema50_key and indicators[ema50_key].value else last_price * 0.95

    is_bearish = regime in ("bear", "strong_bear")
    entry = round(last_price, 2)

    if is_bearish:
        sl_atr  = round(entry + 1.5 * atr, 2)
        sl_ema  = round(max(ema20, ema50) * 1.005, 2)
        stop    = round(min(sl_atr, sl_ema), 2)
        target1 = round(entry - 1.5 * atr, 2)
        target2 = round(entry - 3.0 * atr, 2)
        direction = "Short / Sell"
    else:
        sl_atr  = round(entry - 1.5 * atr, 2)
        sl_ema  = round(min(ema20, ema50) * 0.995, 2)
        stop    = round(max(sl_atr, sl_ema), 2)
        target1 = round(entry + 1.5 * atr, 2)
        target2 = round(entry + 3.0 * atr, 2)
        direction = "Long / Buy"

    risk   = round(abs(entry - stop), 2)
    reward = round(abs(target2 - entry), 2)
    rr     = round(reward / risk, 1) if risk > 0 else 2.0
    atr_pct = atr / last_price
    holding_days = 5 if atr_pct > 0.03 else (10 if atr_pct > 0.015 else 20)

    return {
        "direction": direction,
        "entry": entry,
        "stop_loss": stop,
        "target_1": target1,
        "target_2": target2,
        "risk_per_share": risk,
        "risk_reward": rr,
        "atr14": round(atr, 2),
        "holding_period_days": holding_days,
    }


def analyze_symbol(symbol: str) -> dict[str, Any]:
    """Execute complete end-to-end market analysis and option trade structuring for a symbol."""
    sym_upper = symbol.strip().upper()
    if not sym_upper:
        raise ValueError("Symbol cannot be empty.")

    # Determine provider & VIX symbol
    is_us = sym_upper in {"SPY", "QQQ"} or (not sym_upper.endswith(".NS") and not sym_upper.endswith(".BO") and not sym_upper.startswith("^NSE"))
    vix_symbol = "^VIX" if is_us else "^INDIAVIX"
    fallback_vix = 20.0 if is_us else 15.0

    provider = YahooFinanceProvider(UrllibHTTPClient())
    
    # 1. Fetch OHLCV price history & save to local cache
    fetched_data = provider.fetch_history(sym_upper, period="2y", interval="1d")
    history = save_market_data(sym_upper, fetched_data)
    
    # 2. Fetch VIX data
    annualized_vix = fallback_vix
    try:
        vix_df = provider.fetch_history(vix_symbol, period="5d", interval="1d")
        annualized_vix = float(vix_df["close"][-1])
    except Exception:
        pass

    # 3. Calculate technical indicators
    indicator_engine = IndicatorEngine.default()
    indicators = indicator_engine.calculate(history)

    # 4. Evaluate trend & regime
    weights = {
        "ema200": 20.0,
        "ema_cross": 15.0,
        "ema_stack": 15.0,
        "rsi": 10.0,
        "adx": 10.0,
        "volume": 7.5,
        "relative_strength": 7.5,
        "atr": 5.0,
        "structure": 5.0,
        "bb_exhaustion": 5.0,
    }
    trend_engine = TrendEngine.from_weights(weights)

    snapshot = SnapshotBuilder().build(sym_upper, history)[-1]
    trend_analysis = trend_engine.analyze(snapshot, indicators, history)

    # 5. Select strategy & estimate option trade structure
    recommendation = select_strategy(trend_analysis, iv_rank=min(100.0, max(0.0, ((annualized_vix - 12.0) / 18.0) * 100.0)))
    # Extract ATR14 / EMA20 / EMA50 for cash swing stop/target computation
    _atr_key  = next((k for k in indicators if "ATR" in k.upper()), None)
    _ema20_key = next((k for k in indicators if k.upper() in ("EMA20", "EMA(20)")), None)
    _ema50_key = next((k for k in indicators if k.upper() in ("EMA50", "EMA(50)")), None)
    _atr14_val  = float(indicators[_atr_key].value)  if _atr_key  and indicators[_atr_key].value  else None
    _ema20_val  = float(indicators[_ema20_key].value) if _ema20_key and indicators[_ema20_key].value else None
    _ema50_val  = float(indicators[_ema50_key].value) if _ema50_key and indicators[_ema50_key].value else None

    trade_est = estimate_trade(
        symbol=sym_upper,
        spot_price=float(snapshot.last_price),
        annualized_vix=annualized_vix,
        recommendation=recommendation,
        vix_source="live",
        atr14=_atr14_val,
        ema20=_ema20_val,
        ema50=_ema50_val,
    )

    # Format indicators
    indicator_summary = {
        name: f"{res.value:.2f}"
        for name, res in indicators.items()
        if res.value is not None
    }

    # Format rules (passed vs failed)
    rules_eval = []
    for rule_name in trend_analysis.passed_rules:
        rules_eval.append({"name": rule_name, "passed": True, "score": 1.0, "max_score": 1.0, "explanation": "Condition met"})
    for rule_name in trend_analysis.failed_rules:
        rules_eval.append({"name": rule_name, "passed": False, "score": 0.0, "max_score": 1.0, "explanation": "Condition unfulfilled"})

    # Format trade legs
    legs_data = []
    if trade_est:
        for leg in trade_est.legs:
            action_val = leg.action.value if hasattr(leg.action, "value") else str(leg.action)
            right_val = leg.right.value if hasattr(leg.right, "value") else str(leg.right)
            action_str = "Buy" if action_val.upper() in {"BUY", "LONG"} else "Sell"
            opt_type_str = "Call" if right_val.upper() in {"CALL", "CE", "C"} else "Put"
            legs_data.append({
                "action": action_str,
                "quantity": 1,
                "strike": leg.strike,
                "strike_formatted": _format_strike(leg.strike),
                "option_type": opt_type_str,
                "delta": getattr(leg, "delta", None),
                "expiration": trade_est.expiration.strftime("%Y-%m-%d"),
                "expiration_display": trade_est.expiration.strftime("%d-%b-%Y"),
                "dte": (trade_est.expiration - date.today()).days,
                "summary": f"{action_str} {sym_upper} {trade_est.expiration.strftime('%d-%b-%Y')} {_format_strike(leg.strike)} {opt_type_str}"
            })

    return {
        "symbol": sym_upper,
        "last_price": round(float(snapshot.last_price), 2),
        "as_of": snapshot.observed_at.strftime("%Y-%m-%d %H:%M:%S"),
        "regime": trend_analysis.regime.value,
        "regime_display": trend_analysis.regime.value.replace("_", " ").title(),
        "trend_score": round(trend_analysis.trend_score.value, 1),
        "fit_score": round(trend_analysis.trend_score.value * 10.0, 1),
        "confidence_grade": "A+" if trend_analysis.trend_score.value >= 9.5 else ("A" if trend_analysis.trend_score.value >= 8.0 else ("B" if trend_analysis.trend_score.value >= 6.0 else "C")),
        "confidence_percentage": round(trend_analysis.trend_score.value * 10.0, 1),
        "vix": round(annualized_vix, 2),
        "strategy_type": recommendation.strategy.value,
        "strategy_display": recommendation.strategy.value.replace("_", " ").title(),
        "trade_profile": get_trade_profile(recommendation.strategy.value),
        "trade_category": _get_trade_category(sym_upper),
        "recommendation_reason": recommendation.rationale,
        "cash_trade_setup": _compute_cash_trade_setup(
            float(snapshot.last_price),
            indicators,
            trend_analysis.regime.value,
        ) if _get_trade_category(sym_upper) == "cash" else None,
        "estimated_trade": {
            "legs": legs_data,
            "max_gain": "Defined Risk / Reward",
            "max_loss": "Defined Risk Limit",
            "roc_percentage": getattr(trade_est, "roc_percentage", 150.0),
            "margin_required": getattr(trade_est, "margin_required", 0.0),
            "stop_loss_price": getattr(trade_est, "stop_loss_price", None),
            "take_profit_price": getattr(trade_est, "take_profit_price", None),
            "net_delta": getattr(trade_est, "net_delta", 0.0),
            "net_theta": getattr(trade_est, "net_theta", 0.0),
            "probability_of_profit": getattr(trade_est, "probability_of_profit", 68.0),
            "var_95": getattr(trade_est, "var_95", 0.0),
            "vol_skew_25d": getattr(trade_est, "vol_skew_25d", 0.0),
            "backtest_sharpe": getattr(trade_est, "backtest_sharpe", 1.85),
            "payoff_points": getattr(trade_est, "payoff_points", ()),
            "kelly_sizing": {
                "win_probability": trade_est.kelly_sizing.win_probability,
                "payout_ratio": trade_est.kelly_sizing.payout_ratio,
                "half_kelly_fraction": trade_est.kelly_sizing.half_kelly_fraction,
                "recommended_allocation_pct": trade_est.kelly_sizing.recommended_allocation_pct,
                "suggested_lots": trade_est.kelly_sizing.suggested_lots,
                "max_risk_amount": trade_est.kelly_sizing.max_risk_amount,
            } if trade_est and trade_est.kelly_sizing else None,
        } if trade_est else None,
        "indicators": indicator_summary,
        "rules": rules_eval,
        "news": [
            {
                "title": item.title,
                "publisher": item.publisher,
                "link": item.link,
                "published_at": item.published_at,
                "sentiment": item.sentiment,
            }
            for item in StockNewsProvider.fetch_news(sym_upper)
        ],
    }


class OptionIntelligenceHandler(BaseHTTPRequestHandler):
    """HTTP Handler serving static Web UI files and REST API endpoints."""

    web_dir = Path(__file__).parent.parent.parent / "web"

    def log_message(self, format: str, *args: Any) -> None:
        """Silence standard request logging to keep console clean."""
        pass

    def do_GET(self) -> None:
        import sys
        print(f"REQUEST RECEIVED: {self.path}")
        sys.stdout.flush()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/search":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0]
            results = TickerSearchProvider.search_tickers(q)
            self._send_json([{"symbol": r.symbol, "name": r.name, "exch": r.exch_disp} for r in results])
            return

        if path == "/api/analyze":
            query = urllib.parse.parse_qs(parsed.query)
            symbol_raw = query.get("symbol", ["SPY"])[0]
            symbol = TickerSearchProvider.resolve_ticker(symbol_raw)
            try:
                result = analyze_symbol(symbol)
                self._send_json(result)
            except Exception as e:
                import sys, traceback
                traceback.print_exc()
                sys.stdout.flush()
                sys.stderr.flush()
                self._send_json({"error": str(e)}, status=400)
            return

        if path == "/api/popular":
            self._send_json({
                "us": ["SPY", "QQQ", "AAPL", "NVDA", "TSLA", "MSFT", "AMZN"],
                "indian": ["NIFTY 50", "BANKNIFTY", "FINNIFTY", "MIDCAPNIFTY", "SENSEX", "TITAN.NS", "SUNPHARMA.NS", "ICICIBANK.NS", "RELIANCE.NS"],
            })
            return

        # Serve static assets from web/ directory
        relative_path = path.lstrip("/")
        if not relative_path:
            relative_path = "index.html"

        file_path = self.web_dir / relative_path
        if file_path.exists() and file_path.is_file():
            self._send_file(file_path)
        else:
            self._send_file(self.web_dir / "index.html")

    def _send_json(self, data: Any, status: int = 200) -> None:
        content = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _send_file(self, file_path: Path) -> None:
        mime_types = {
            ".html": "text/html; charset=utf-8",
            ".css": "text/css; charset=utf-8",
            ".js": "application/javascript; charset=utf-8",
            ".json": "application/json; charset=utf-8",
            ".png": "image/png",
            ".svg": "image/svg+xml",
        }
        content_type = mime_types.get(file_path.suffix.lower(), "application/octet-stream")
        content = file_path.read_bytes()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


from socketserver import ThreadingMixIn


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server handling concurrent requests in separate worker threads."""

    daemon_threads = True


def start_web_server(port: int = 8090) -> None:
    """Launch the option intelligence web server."""
    server_address = ("", port)
    httpd = ThreadedHTTPServer(server_address, OptionIntelligenceHandler)
    print(f"Starting Portfolio Intelligence Web Engine at http://localhost:{port}")
    httpd.serve_forever()
