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
        # Load list of subscriber chat IDs from a separate JSON file (default path config/telegram_subscribers.json)
        self.telegram_subscribers = self._load_telegram_subscribers()
        # Fallback to single chat ID from env for backward compatibility
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
            f"• *Timestamp*: {now_str}\n"
            f"• *Expiry*: {market_row.get('expiration').isoformat() if isinstance(market_row.get('expiration'), datetime) else market_row.get('expiration')}"
        )

    def send_telegram(self, message: str) -> bool:
        """Send notification via Telegram Bot API."""
        if not self.telegram_token:
            return False
        if not self.telegram_token:
            return False
        # Use subscriber list if available, otherwise fallback to single chat ID
        successes = []
        # If a list of subscribers is loaded, send to each; otherwise use the single chat_id
        targets = self.telegram_subscribers if self.telegram_subscribers else []
        if not targets and self.telegram_chat_id:
            targets = [self.telegram_chat_id]
        if not targets:
            return False
        for chat_id in targets:
            url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "Markdown",
            }
            success = self._http_post(url, payload)
            successes.append(success)
        # Return True only if at least one message was sent successfully
        return any(successes)

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

    def dispatch_high_conviction_alert(self, market_row: dict[str, Any]) -> dict[str, bool]:
        """Dispatch real-time alert only if fit_score >= 8.0/10."""
        score = market_row.get("fit_score", market_row.get("score", 0.0))
        if isinstance(score, (int, float)) and score > 10.0:
            score = score / 10.0
        if score >= 8.0:
            return self.dispatch_all(market_row)
        return {"telegram": False, "slack": False, "discord": False}

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
    def _load_telegram_subscribers(self, path: str = None) -> list[str]:
        """Load Telegram subscriber chat IDs from a JSON file.
        The file can be a simple list like ["12345", "67890"] or an object
        {"subscribers": ["12345", "67890"]}. Returns an empty list on any error.
        """
        if path is None:
            # Resolve default path relative to project root (config/telegram_subscribers.json)
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
            path = os.path.join(base_dir, "config", "telegram_subscribers.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(item) for item in data]
                if isinstance(data, dict) and "subscribers" in data:
                    return [str(item) for item in data["subscribers"]]
        except Exception:
            return []
