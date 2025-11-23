# Altea Gym Booking Bot

Automated booking script for Altea Active classes using browser automation.

## Features

- 🤖 Automated login and booking via headless browser
- 📅 Schedule-based class booking (runs via cron)
- 🔒 Secure credential management via config file
- 🐧 Linux server compatible (headless Chromium)
- 📧 Email notifications via Mailgun (success/failure alerts)

## Quick Setup

### 1. Run the setup script

```bash
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Install Playwright's Chromium browser
- Create a `config.yaml` template

### 2. Configure your credentials

Copy `env.example` to `.env`:

```bash
cp env.example .env
```

Edit `.env` with your credentials:

```bash
# Altea Active Credentials (required)
ALTEA_EMAIL=your-email@example.com
ALTEA_PASSWORD=your-password-here

# Mailgun Configuration (optional - for email notifications)
MAILGUN_DOMAIN=your-mailgun-domain.mailgun.org
MAILGUN_API_KEY=key-your-api-key-here
FROM_EMAIL=altea-booking@your-domain.com
TO_EMAIL=your-email@example.com
WIFE_EMAIL=wife-email@example.com  # Optional
```

**Note:** Email notifications are optional. If you don't configure Mailgun, the script will still work but won't send emails.

### 3. Test the script

```bash
source venv/bin/activate
python main.py
```

## Manual Setup (if setup.sh doesn't work)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browser
playwright install chromium

# On Linux, also install system dependencies
playwright install-deps chromium  # Linux only
```

## Running on a Schedule (Cron)

To automatically book classes when the booking window opens:

```bash
crontab -e
```

Add this line (adjust paths and timing as needed):

```
# Run every day at 9 AM
0 9 * * * cd /path/to/altea-book && /path/to/altea-book/venv/bin/python /path/to/altea-book/main.py >> /path/to/altea-book/booking.log 2>&1
```

## Design

See [design.md](design.md) for architectural details.

## Troubleshooting

### "Browser executable not found"
Run: `playwright install chromium`

### "Permission denied: ./setup.sh"
Run: `chmod +x setup.sh`

### Script fails on Linux server
Make sure system dependencies are installed:
```bash
playwright install-deps chromium
```

## Email Notifications

The bot sends email notifications for:
- ✅ **Successful bookings** - Confirms class, date, time, and spots left
- ❌ **Failed bookings** - Includes error details and troubleshooting info
- 👥 **Wife bookings** - Sends to both you and your wife when booking for her

Email notifications use [Mailgun](https://www.mailgun.com/) API. You'll need:
1. A Mailgun account (free tier available)
2. A verified domain or use Mailgun's sandbox domain
3. Your API key from the Mailgun dashboard

## Security Notes

- Never commit `.env` with real credentials
- The `.gitignore` file excludes the `.env` file
- All credentials are stored locally in `.env`
- Use environment variables for all sensitive configuration

## License

For personal use only.
