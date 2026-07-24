"""Webhook Alert Dispatcher for Telegram, Slack, Discord, and Custom Webhooks."""

import json
import os
import urllib.request
from datetime import UTC, datetime, timedelta
from typing import Any, Optional


class NotificationDispatcher:
    """Dispatches real-time signal alerts to webhooks and messaging channels."""

    def __init__(
        self,
        telegram_token: Optional[str] = None,
        telegram_chat_id: Optional[str] = None,
        slack_url: Optional[str] = None,
        discord_url: Optional[str] = None,
    ):
        self.telegram_token = telegram_token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.telegram_chat_id = telegram_chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self.slack_url = slack_url or os.environ.get("SLACK_WEBHOOK_URL")
        self.discord_url = discord_url or os.environ.get("DISCORD_WEBHOOK_URL")

    def format_signal_message(self, market_row: dict[str, Any]) -> str:
        """Format a market signal row into a clean alert message."""
        market = market_row.get("market", market_row.get("symbol", "N/A"))
        strategy_name = market_row.get("strategy_name", market_row.get("trend", "N/A"))
        score = market_row.get("fit_score", market_row.get("score", 0.0))
        if isinstance(score, (int, float)) and score > 10.0:
            score = round(score / 10.0, 1)
        strategy_structure = market_row.get("strategy", "").replace("<br>", "\n  ")
        signal = market_row.get("signal", "Signal Update")
        ist_now = datetime.now(UTC) + timedelta(hours=5, minutes=30)
        now_str = ist_now.strftime("%Y-%m-%d %H:%M IST")

        return (
            f"🚨 *PORTFOLIO INTELLIGENCE ALERT*\n"
            f"• *Market*: {market}\n"
            f"• *Regime/Strategy*: {strategy_name}\n"
            f"• *Score*: {score}/10\n"
            f"• *Signal*: {signal}\n"
            f"• *Structure*:\n  {strategy_structure}\n"
            f"• *Timestamp*: {now_str}"
        )

    def send_telegram(self, message: str) -> bool:
        """Send notification via Telegram Bot API."""
        if not self.telegram_token or not self.telegram_chat_id:
            return False
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }
        return self._http_post(url, payload)

    def send_slack(self, message: str) -> bool:
        """Send notification via Slack Webhook."""
        if not self.slack_url:
            return False
        payload = {"text": message}
        return self._http_post(self.slack_url, payload)

    def send_discord(self, message: str) -> bool:
        """Send notification via Discord Webhook."""
        if not self.discord_url:
            return False
        payload = {"content": message}
        return self._http_post(self.discord_url, payload)

    def dispatch_all(self, market_row: dict[str, Any]) -> dict[str, bool]:
        """Dispatch signal message to all configured webhooks."""
        message = self.format_signal_message(market_row)
        results = {
            "telegram": self.send_telegram(message),
            "slack": self.send_slack(message),
            "discord": self.send_discord(message),
        }
        return results

    def _http_post(self, url: str, data: dict) -> bool:
        """Helper for making synchronous HTTP POST requests."""
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                return 200 <= resp.status < 300
        except Exception:
            return False
