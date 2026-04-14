# Indian IPO Subscription Tracker Bot

A Python bot that scrapes mainboard IPO subscription data from [chittorgarh.com](https://www.chittorgarh.com), applies configurable alert rules, and sends notifications via WhatsApp.

## How it works

1. **Scrapes** the Chittorgarh IPO dashboard to discover mainboard IPOs
2. **Fetches** each IPO's subscription page and parses category-wise subscription data (QIB, sNII, bNII, Retail, Total)
3. **Filters** based on configurable rules (mainboard only, last-day only, subscription thresholds)
4. **Sends** a formatted WhatsApp message with matching IPO subscription details

## Setup

### Prerequisites

- Python 3.9+
- Google Chrome (for WhatsApp Web via pywhatkit)

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure

Edit `config.yaml`:

```yaml
scraper:
  base_url: "https://www.chittorgarh.com"
  year: 2026

filters:
  ipo_type: "mainboard"      # only mainboard IPOs (skip SME)
  only_last_day: true         # only IPOs whose close date is today

alert_rules:
  min_total_subscription: 1.0 # minimum total subscription (x times)
  min_qib_subscription: 0     # minimum QIB subscription (0 = no filter)
  min_retail_subscription: 0   # minimum Retail subscription (0 = no filter)

whatsapp:
  phone_number: "+91XXXXXXXXXX"  # your recipient's number with country code
  wait_time: 15
  close_tab: true
```

**Important:** Replace `+91XXXXXXXXXX` with the actual WhatsApp phone number you want to send alerts to.

### WhatsApp first-time setup

The bot uses `pywhatkit` which automates WhatsApp Web through your browser:

1. Open Chrome and go to [web.whatsapp.com](https://web.whatsapp.com)
2. Scan the QR code with your phone to log in
3. Keep the session active — `pywhatkit` will open new tabs to send messages

## Usage

### Run manually (dry run — prints to screen, no WhatsApp)

```bash
python -m src.main --dry-run --skip-date-filter
```

### Run for today's closing IPOs (sends WhatsApp if configured)

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

## Schedule with cron

To run the bot every weekday at 4:30 PM IST (when last-day subscription data is mostly finalized):

```bash
crontab -e
```

Add this line (adjust the Python path and project path as needed):

```
30 16 * * 1-5 cd /Users/r0b070d/Downloads/IPO_Tracker && /usr/bin/python3 -m src.main >> logs/ipo_tracker.log 2>&1
```

Make sure the `logs/` directory exists:

```bash
mkdir -p logs
```

## Project structure

```
IPO_Tracker/
├── config.yaml         # Alert rules, scraper settings, WhatsApp config
├── requirements.txt    # Python dependencies
├── README.md
├── logs/               # Log output from cron runs
└── src/
    ├── __init__.py
    ├── main.py         # Entry point — scrape → filter → notify
    ├── scraper.py      # Scrapes chittorgarh.com for IPO subscription data
    ├── rules.py        # Applies filtering rules from config
    ├── notifier.py     # Sends WhatsApp messages via pywhatkit
    └── models.py       # Data classes (IPOSubscription, AlertMessage)
```
