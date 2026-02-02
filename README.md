# Metal Price Tracker

A Python-based notification system that monitors gold and silver prices from [Aura Gold](https://auragold.netlify.app/) and sends email/SMS alerts when prices drop by 10% or 20%.

## Features

- **Live Price Tracking**: Fetches real-time gold and silver prices with 3% GST
- **Price Drop Alerts**: Notifies when prices fall 10% or 20% from your baseline
- **Email Notifications**: Using Resend (free tier: 100 emails/day)
- **SMS Notifications**: Using Textbelt (free tier: 1 SMS/day for testing)
- **Daemon Mode**: Run continuously with scheduled price checks
- **Smart Alerts**: Prevents duplicate notifications for the same threshold

## Quick Start

### 1. Install Dependencies

```bash
cd "metal price tracker"
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

### 3. Get API Keys

#### Email (Resend - Free Tier)
1. Sign up at [resend.com](https://resend.com)
2. Create an API key
3. Add to `.env`: `RESEND_API_KEY=re_xxxx`

#### SMS (Textbelt - Free Tier)
- Free tier uses key `textbelt` (1 SMS/day)
- For more SMS, consider [Twilio](https://twilio.com) trial

### 4. Set Your Baseline Price

```bash
python main.py --set-baseline
```

This captures the current gold and silver prices as your reference point.

### 5. Run the Tracker

```bash
# Run once to check prices
python main.py

# Run continuously (checks every 30 minutes)
python main.py --daemon

# Check status
python main.py --status
```

## Configuration Options

Edit `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `RESEND_API_KEY` | Resend API key for emails | - |
| `EMAIL_TO` | Email address for notifications | - |
| `PHONE_NUMBER` | Phone number for SMS (with country code) | - |
| `TEXTBELT_KEY` | Textbelt API key | `textbelt` |
| `ALERT_10_PERCENT` | Enable 10% drop alerts | `true` |
| `ALERT_20_PERCENT` | Enable 20% drop alerts | `true` |
| `CHECK_INTERVAL_MINUTES` | Check frequency in daemon mode | `30` |
| `GOLD_BASELINE_PRICE` | Manual baseline for gold | auto |
| `SILVER_BASELINE_PRICE` | Manual baseline for silver | auto |

## Running as a Cron Job

For production use, set up a cron job instead of daemon mode:

```bash
# Edit crontab
crontab -e

# Add this line to check every 30 minutes
*/30 * * * * cd /path/to/metal-price-tracker && /usr/bin/python3 main.py >> /var/log/metal-tracker.log 2>&1
```

## Running as a Systemd Service

Create `/etc/systemd/system/metal-tracker.service`:

```ini
[Unit]
Description=Metal Price Tracker
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/metal-price-tracker
ExecStart=/usr/bin/python3 main.py --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable metal-tracker
sudo systemctl start metal-tracker
```

## API Data Source

Data is fetched from Aura Gold API:
- **Gold**: `https://auragold.netlify.app/api/prices?metal=gold`
- **Silver**: `https://auragold.netlify.app/api/prices?metal=silver`

### Response Format

```json
{
  "success": true,
  "data": [
    {
      "product_name": "Aura Digital Gold 24K",
      "price_with_gst": 14078.65,
      "price_without_gst": 13668.59,
      "aura_buy_price": 13668.59,
      "aura_sell_price": 13399.92,
      "updated_at": "2026-01-05T00:00:17"
    }
  ]
}
```

## Command Reference

| Command | Description |
|---------|-------------|
| `python main.py` | Check prices once |
| `python main.py --daemon` | Run continuously |
| `python main.py --set-baseline` | Set current prices as baseline |
| `python main.py --reset-alerts` | Reset alert state (allows re-notification) |
| `python main.py --status` | Show current configuration and prices |

## Free Tier Limits

| Service | Free Tier Limit |
|---------|-----------------|
| Resend | 100 emails/day |
| Textbelt | 1 SMS/day (testing) |

## Alternative SMS Services

For production SMS needs, consider:
- **Twilio**: Trial account with free credits
- **AWS SNS**: Pay-per-use, very affordable
- **Vonage**: Free trial available

## License

MIT License - Feel free to modify and distribute.
