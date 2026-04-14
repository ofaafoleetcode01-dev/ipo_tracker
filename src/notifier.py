from __future__ import annotations

import logging

import requests

from src.models import AlertMessage

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _validate_config(config: dict) -> tuple[str, str] | None:
    """Return (token, chat_id) or None if not configured."""
    tg_cfg = config.get("telegram", {})
    token = tg_cfg.get("bot_token", "")
    chat_id = tg_cfg.get("chat_id", "")

    if not token or token == "YOUR_BOT_TOKEN_HERE":
        logger.error("Telegram bot token not configured.")
        return None
    if not chat_id or str(chat_id) == "YOUR_CHAT_ID_HERE":
        logger.error("Telegram chat_id not configured.")
        return None
    return token, str(chat_id)


def _send_message(token: str, chat_id: str, text: str) -> bool:
    """Low-level send via Telegram Bot API."""
    url = _TELEGRAM_API.format(token=token)
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}

    try:
        logger.info("Sending Telegram message to chat %s ...", chat_id)
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            logger.info("Telegram message sent successfully")
            return True
        logger.error("Telegram API error: %s", result.get("description", result))
        return False
    except Exception:
        logger.exception("Failed to send Telegram message")
        return False


def send_telegram(alert: AlertMessage, config: dict) -> bool:
    """Send the formatted alert as a Telegram message."""
    message = alert.format()
    if not message:
        logger.info("No alert message to send (empty)")
        return False

    creds = _validate_config(config)
    if not creds:
        print("\n--- Telegram message (not sent, not configured) ---")
        print(message)
        print("---")
        return False

    return _send_message(*creds, message)


def send_telegram_text(text: str, config: dict) -> bool:
    """Send a plain text message via Telegram."""
    creds = _validate_config(config)
    if not creds:
        print("\n--- Telegram message (not sent, not configured) ---")
        print(text)
        print("---")
        return False

    return _send_message(*creds, text)
