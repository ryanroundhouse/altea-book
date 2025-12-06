# Altea Gym Booking Bot

Automated booking script for Altea Active classes using browser automation.

> **Quick Start**: New to this? See [QUICK_START.md](QUICK_START.md) for a 5-minute setup guide.
>
> **Scheduling Guide**: Learn how to set up automatic weekly bookings in [SCHEDULING_GUIDE.md](SCHEDULING_GUIDE.md).

## Features

- 🤖 Automated login and booking via headless browser
- 📅 Weekly schedule-based booking with automatic cron setup
- 🔒 Secure credential management via config file
- 🐧 Linux server compatible (headless Chromium)
- 📧 Email notifications via Mailgun (success/failure alerts)
- ⚙️ YAML configuration for recurring weekly classes

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

### 2. Configure your users

Copy `users.example.yaml` to `users.yaml`:

```bash
cp users.example.yaml users.yaml
```

Edit `users.yaml` with your Altea credentials:

```yaml
users:
  ryan:
    altea_email: ryan@example.com
    altea_password: your-password-here
    notification_email: ryan@example.com
  
  katie:
    altea_email: katie@example.com
    altea_password: her-password-here
    notification_email: katie@example.com
```

### 3. Configure email notifications (optional)

Copy `env.example` to `.env`:

```bash
cp env.example .env
```

Edit `.env` with Mailgun credentials:

```bash
MAILGUN_DOMAIN=your-mailgun-domain.mailgun.org
MAILGUN_API_KEY=key-your-api-key-here
FROM_EMAIL=altea-booking@your-domain.com
```

**Note:** Email notifications are optional. If you don't configure Mailgun, the script will still work but won't send emails.

### 4. Configure your weekly classes

Edit `classes.yaml` to define which classes you want each week:

```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    user: ryan  # Must match a user in users.yaml
```

**Booking Rule**: All classes automatically book 7 days and 1 hour before the class time. For example, a Monday 4:30 PM class will be booked on the previous Monday at 3:30 PM.

### 5. Test the script

Manual booking for a specific date:
```bash
source venv/bin/activate
python main.py "29-11-2025" "8:30 AM" "LF3 Strong" --user ryan
```

Or test booking from your configuration:
```bash
python book_from_config.py --date 2025-12-02 --dry-run
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

## Automatic Scheduling with Cron

The scheduler automatically sets up cron jobs based on your `classes.yaml` configuration.

### View what would be scheduled:

```bash
python scheduler.py --dry-run
```

### Install the cron jobs:

```bash
python scheduler.py --install
```

This will:
- Read your `classes.yaml` configuration
- Calculate when each booking window opens
- Install cron jobs to automatically book classes at the right time
- Create logs in the `logs/` directory

### Remove installed cron jobs:

```bash
python scheduler.py --remove
```

### View your scheduled jobs:

```bash
crontab -l
```

## Usage Examples

### Manual Booking

Book a specific class on a specific date:

```bash
# Book for ryan
python main.py "29-11-2025" "8:30 AM" "LF3 Strong" --user ryan

# Book for katie
python main.py "29-11-2025" "8:30 AM" "LF3 Strong" --user katie
```

### Config-Based Booking

Book based on your weekly schedule configuration:

```bash
# Book class for next Monday (based on classes.yaml)
python book_from_config.py --date 2025-12-02

# Dry run to see what would be booked
python book_from_config.py --date 2025-12-02 --dry-run
```

## How It Works

### The Complete Workflow

1. **Configure your weekly schedule** (`classes.yaml`):
   - Define which classes you want on which days
   - Booking windows are automatically calculated (7 days and 1 hour before)

2. **Set up automatic scheduling** (`scheduler.py`):
   - Reads your configuration
   - Calculates booking times (class time minus 1 hour, 7 days before)
   - Installs cron jobs that trigger at booking window openings

3. **Automatic booking** (`book_from_config.py`):
   - Triggered by cron at the right time
   - Reads the configuration to know what to book
   - Calculates the target date (e.g., 7 days from now)
   - Books the class automatically
   - Sends email notifications

### Example

You want to book "LF3 Strong" every Monday at 4:30 PM. Booking opens the previous Monday at 3:30 PM.

**Step 1:** Add to `classes.yaml`:
```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    user: ryan
```

The system automatically calculates that booking opens 7 days and 1 hour before (3:30 PM).

**Step 2:** Install the scheduler:
```bash
python scheduler.py --install
```

**Result:** Every Monday at 3:30 PM, the system will automatically book "LF3 Strong" for the following Monday at 4:30 PM.

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

Each user receives notifications at their configured `notification_email` in `users.yaml`.

Email notifications use [Mailgun](https://www.mailgun.com/) API. You'll need:
1. A Mailgun account (free tier available)
2. A verified domain or use Mailgun's sandbox domain
3. Your API key from the Mailgun dashboard

## Security Notes

- Never commit `.env` or `users.yaml` with real credentials
- The `.gitignore` file excludes both `.env` and `users.yaml`
- User credentials (Altea login) are stored in `users.yaml`
- Mailgun API keys are stored in `.env`

## License

For personal use only.
