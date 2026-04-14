# Indian IPO Subscription Tracker Bot

A Python bot that scrapes mainboard IPO subscription data from [chittorgarh.com](https://www.chittorgarh.com), applies configurable alert rules, and sends notifications via Telegram.

## How it works

1. **Scrapes** the Chittorgarh IPO dashboard to discover mainboard IPOs
2. **Fetches** each IPO's subscription page and parses category-wise subscription data (QIB, sNII, bNII, Retail, Total)
3. **Filters** based on configurable rules (mainboard only, last-day only, subscription thresholds)
4. **Sends** a formatted Telegram message with matching IPO subscription details

## Setup

### Prerequisites

- Python 3.9+

### Install dependencies

```bash
pip install -r requirements.txt
```

### Telegram bot setup

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`, pick a name and username
3. Copy the bot token it gives you (looks like `123456:ABC-DEF...`)
4. Send any message to your new bot on Telegram
5. Run the setup helper to auto-detect your chat ID:

```bash
python setup_telegram.py
```

This will find your chat ID, save it to `config.yaml`, and send a test message.

### Configure

Edit `config.yaml`:

```yaml
scraper:
  base_url: "https://www.chittorgarh.com"
  year: 2026

filters:
  ipo_type: "mainboard"        # only mainboard IPOs (skip SME)
  only_last_day: true          # only IPOs whose close date is today

alert_rules:
  min_total_subscription: 1.0  # minimum total subscription (x times)
  min_qib_subscription: 0      # minimum QIB subscription (0 = no filter)
  min_retail_subscription: 0   # minimum Retail subscription (0 = no filter)

telegram:
  bot_token: "YOUR_BOT_TOKEN_HERE"  # from @BotFather
  chat_id: "YOUR_CHAT_ID_HERE"      # auto-detected by setup_telegram.py
```

## Usage

### Run manually (dry run — prints to screen, no Telegram)

```bash
python -m src.main --dry-run --skip-date-filter
```

### Run for today's closing IPOs (sends Telegram if configured)

```bash
python -m src.main
```

### Run with verbose logging

```bash
python -m src.main -v
```

### CLI flags

| Flag                | Description                                                |
|---------------------|------------------------------------------------------------|
| `--dry-run`         | Scrape and filter but print message instead of sending     |
| `--skip-date-filter`| Ignore the "only last day" filter (useful for testing)     |
| `-v, --verbose`     | Enable debug-level logging                                 |
| `-c, --config PATH` | Use a custom config file (default: `config.yaml`)         |

## Jupyter notebook

`test_code.ipynb` provides an interactive environment to run each step individually — scrape, view as a table, filter, and preview the alert message.

## Schedule with cron

To run the bot every weekday at 4:30 PM IST (when last-day subscription data is mostly finalized):

```bash
crontab -e
```

Add this line (adjust the Python path and project path as needed):

```
30 16 * * 1-5 cd /path/to/IPO_Tracker && python3 -m src.main >> logs/ipo_tracker.log 2>&1
```

Make sure the `logs/` directory exists:

```bash
mkdir -p logs
```

## Project structure

```
IPO_Tracker/
├── config.yaml          # Alert rules, scraper settings, Telegram config
├── requirements.txt     # Python dependencies
├── setup_telegram.py    # One-time helper to detect Telegram chat ID
├── test_code.ipynb      # Interactive Jupyter notebook for testing
├── README.md
├── logs/                # Log output from cron runs
└── src/
    ├── __init__.py
    ├── main.py          # Entry point — scrape → filter → notify
    ├── scraper.py       # Scrapes chittorgarh.com for IPO subscription data
    ├── rules.py         # Applies filtering rules from config
    ├── notifier.py      # Sends Telegram messages via Bot API
    └── models.py        # Data classes (IPOSubscription, AlertMessage)
```
