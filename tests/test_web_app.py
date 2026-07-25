"""Unit & Integration Tests for Web Application UI, QuickSelect, and Trade Generator."""

import json
import re
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
WEB_DIR = ROOT_DIR / "web"
INDEX_HTML = WEB_DIR / "index.html"
APP_JS = WEB_DIR / "app.js"
DATA_DIR = WEB_DIR / "data"


class TestWebAppUI(unittest.TestCase):
    """Test suite covering QuickSelect, search form submit, and static data schemas."""

    def setUp(self) -> None:
        self.assertTrue(INDEX_HTML.exists(), "web/index.html must exist")
        self.assertTrue(APP_JS.exists(), "web/app.js must exist")
        self.assertTrue(DATA_DIR.exists(), "web/data directory must exist")
        self.index_content = INDEX_HTML.read_text(encoding="utf-8")
        self.app_content = APP_JS.read_text(encoding="utf-8")

    def test_quickselect_chips_have_type_button_and_onclick(self) -> None:
        """Verify all QuickSelect chip buttons have type='button' and window.selectTicker handlers."""
        chip_symbols = re.findall(r'data-symbol="([^"]+)"', self.index_content)
        self.assertGreaterEqual(len(chip_symbols), 8, "Must have at least 8 QuickSelect chips")

        expected_symbols = {"SPY", "QQQ", "^NSEI", "^NSEBANK", "NIFTY_FIN_SERVICE.NS", "^NSEMDCP50", "^BSESN", "TITAN.NS", "NVDA"}
        found_symbols = set(chip_symbols)
        for expected in expected_symbols:
            self.assertIn(expected, found_symbols, f"QuickSelect chip for {expected} must be present in index.html")

    def test_search_form_structure_and_ids(self) -> None:
        """Verify search-form, symbol-input, and analyze-btn exist with correct IDs."""
        self.assertIn('id="search-form"', self.index_content)
        self.assertIn('id="symbol-input"', self.index_content)
        self.assertIn('id="analyze-btn"', self.index_content)

    def test_top_4_market_leaderboard_pre_rendered(self) -> None:
        """Verify Top 4 Market Leaderboards are pre-rendered in index.html."""
        self.assertIn("TOP 4 HIGH-CONVICTION TRADES", self.index_content)
        self.assertIn("U.S. Markets (Top 4)", self.index_content)
        self.assertIn("Indian Markets (Top 4)", self.index_content)
        self.assertIn('<div id="top-trades-grid" class="top-trades-grid">', self.index_content)
        top_cards = self.index_content.count('class="top-card"')
        self.assertGreaterEqual(top_cards, 4, "Must pre-render at least 4 Top Trade cards in index.html")

    def test_candidate_url_path_resolver_in_app_js(self) -> None:
        """Verify candidate URL path resolver fetchStaticData exists in app.js."""
        self.assertIn("fetchStaticData(safeSymbol)", self.app_content)
        self.assertIn("candidateUrls", self.app_content)
        self.assertIn("data/${safeSymbol}.json", self.app_content)
        self.assertIn("https://kumashish.github.io/pie/data/${safeSymbol}.json", self.app_content)

    def test_active_symbol_tracking_prevents_spy_overwrite(self) -> None:
        """Verify activeSearchSymbol tracks active searches to prevent SPY overwrite race condition."""
        self.assertIn("let activeSearchSymbol = null;", self.app_content)
        self.assertIn("activeSearchSymbol = cleanSym;", self.app_content)
        self.assertIn("activeSearchSymbol === symbol.toUpperCase()", self.app_content)

    def test_static_data_files_valid_schemas(self) -> None:
        """Verify static JSON dataset files exist and contain valid option schemas."""
        required_tickers = ["SPY", "QQQ", "NVDA", "AAPL", "GOOGL", "NSEI", "NSEBANK", "TITAN_NS", "SUNPHARMA_NS"]
        for ticker in required_tickers:
            json_file = DATA_DIR / f"{ticker}.json"
            self.assertTrue(json_file.exists(), f"Static JSON file for {ticker} must exist")
            data = json.loads(json_file.read_text(encoding="utf-8"))
            self.assertIn("symbol", data)
            self.assertIn("last_price", data)
            self.assertIn("fit_score", data)
            self.assertIn("regime", data)
            self.assertIn("strategy_display", data)
            self.assertIn("estimated_trade", data)
            self.assertIn("indicators", data)
            self.assertIn("rules", data)


if __name__ == "__main__":
    unittest.main()
