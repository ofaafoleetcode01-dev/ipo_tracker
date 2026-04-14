from __future__ import annotations

import logging

import requests

from src.models import AlertMessage

logger = logging.getLogger(__name__)

_TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_telegram(alert: AlertMessage, config: dict) -> bool:
    """Send the alert as a Telegram message.

    Returns True on success, False on failure.
    """
    message = alert.format()
    if not message:
        logger.info("No alert message to send (empty)")
        return False

    tg_cfg = config.get("telegram", {})
    token = tg_cfg.get("bot_token", "")
    chat_id = tg_cfg.get("chat_id", "")

    if not token or token == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "Telegram bot token not configured. "
            "Update 'telegram.bot_token' in config.yaml"
        )
        print("\n--- Telegram message (not sent, bot_token not configured) ---")
        print(message)
        print("---")
        return False

    if not chat_id or str(chat_id) == "YOUR_CHAT_ID_HERE":
        logger.error(
            "Telegram chat_id not configured. "
            "Update 'telegram.chat_id' in config.yaml"
        )
        print("\n--- Telegram message (not sent, chat_id not configured) ---")
        print(message)
        print("---")
        return False

    url = _TELEGRAM_API.format(token=token)
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        logger.info("Sending Telegram message to chat %s ...", chat_id)
        resp = requests.post(url, json=payload, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("ok"):
            logger.info("Telegram message sent successfully")
            return True
        else:
            logger.error("Telegram API error: %s", result.get("description", result))
            return False
    except Exception:
        logger.exception("Failed to send Telegram message")
        return False
