"""Helper to detect your Telegram chat ID and update config.yaml.

Usage:
  1. Create a bot via @BotFather and paste the token into config.yaml
  2. Send any message to your bot on Telegram
  3. Run: python setup_telegram.py
"""
from pathlib import Path

import requests
import yaml

CONFIG_PATH = Path(__file__).parent / "config.yaml"


def main() -> None:
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    token = config.get("telegram", {}).get("bot_token", "")
    if not token or token == "YOUR_BOT_TOKEN_HERE":
        print("Put your bot token in config.yaml first (telegram.bot_token)")
        return

    print(f"Using bot token: {token[:10]}...{token[-5:]}")
    print("Checking for messages sent to your bot ...")

    resp = requests.get(
        f"https://api.telegram.org/bot{token}/getUpdates", timeout=10
    )
    data = resp.json()

    if not data.get("ok") or not data.get("result"):
        print("\nNo messages found. Please send any message to your bot on Telegram first, then re-run this script.")
        return

    msg = data["result"][-1].get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    chat_name = msg.get("chat", {}).get("first_name", "Unknown")

    if not chat_id:
        print("Could not find a chat ID. Send a message to the bot and retry.")
        return

    print(f"\nDetected chat: {chat_name} (ID: {chat_id})")

    config["telegram"]["chat_id"] = str(chat_id)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"Updated config.yaml with chat_id: {chat_id}")
    print("\nSending test message ...")

    test_msg = "IPO Tracker Bot is connected! You'll receive IPO subscription alerts here."
    send_resp = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={"chat_id": chat_id, "text": test_msg},
        timeout=10,
    )
    if send_resp.json().get("ok"):
        print("Test message sent! Check your Telegram.")
    else:
        print(f"Failed: {send_resp.json()}")


if __name__ == "__main__":
    main()
