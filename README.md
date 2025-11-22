# Altea Gym Booking Bot

Automated booking script for Altea Active classes using browser automation.

## Features

- 🤖 Automated login and booking via headless browser
- 📅 Schedule-based class booking (runs via cron)
- 🔒 Secure credential management via config file
- 🐧 Linux server compatible (headless Chromium)
- 📧 Email notifications (coming soon)

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

Edit `config.yaml`:

```yaml
credentials:
  email: "your-email@example.com"
  password: "your-password"
```

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

## Security Notes

- Never commit `config.yaml` with real credentials
- The `.gitignore` file excludes sensitive files
- Credentials are only stored locally

## License

For personal use only.
