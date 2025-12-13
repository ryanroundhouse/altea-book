# Altea Gym Booking Bot

Automated booking script for Altea Active classes using browser automation (Playwright). Configure your weekly schedule in YAML, optionally add email notifications, and install cron jobs to auto-book at the booking window open time.

## Features

- **Automated booking**: Headless browser login + class booking.
- **Weekly scheduling**: Define recurring classes in `classes.yaml`; install cron jobs with `scheduler.py`.
- **Multi-user**: Book for multiple users with separate credentials in `users.yaml`.
- **Notifications (optional)**: Mailgun success/failure emails.
- **Calendar events (optional)**: Send booked-class details to a Google Apps Script webhook to create calendar events.
- **Cross-platform**: macOS + Linux supported (headless Chromium).

## Quick start

### Prerequisites

- **Python**: Use the version your environment supports (this repo includes a local `venv/` in some setups).
- **Playwright browser**: Chromium is required for automation.

### 1) Run the setup script

```bash
./setup.sh
```

If `./setup.sh` fails, see **Manual setup** below.

### 2) Configure users (`users.yaml`)

```bash
cp users.example.yaml users.yaml
```

Example:

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

### 3) Configure classes (`classes.yaml`)

Example:

```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong" # partial match works
    user: ryan         # must match a user in users.yaml
```

### 4) Dry-run the schedule and booking

```bash
source venv/bin/activate

# Preview cron jobs that would be created
python scheduler.py --dry-run

# Test booking logic for a given date (no booking)
python book_from_config.py --date 2025-12-02 --dry-run
```

### 5) Install automatic scheduling (cron)

```bash
python scheduler.py --install
```

## Manual setup (if `setup.sh` doesn’t work)

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

playwright install chromium

# Linux only:
playwright install-deps chromium
```

## Configuration reference

### `users.yaml`

Fields:
- **`altea_email`**: Altea login email
- **`altea_password`**: Altea login password
- **`notification_email`**: Where to send email notifications (if configured)
- **`calendar_webhook_url`** (optional): Google Apps Script web app URL to create calendar events

Example:

```yaml
users:
  ryan:
    altea_email: ryan@example.com
    altea_password: your-password
    notification_email: ryan@example.com
    calendar_webhook_url: https://script.google.com/macros/s/AKfycb...xyz/exec
```

### `classes.yaml`

Each entry:

```yaml
- day: Monday              # Day of week for the class
  time: "4:30 PM"          # Local time (12-hour format)
  name: "LF3 Strong"       # Class name (partial match works)
  user: ryan               # User key from users.yaml
```

## Booking rule (important)

All classes are booked **7 days and 1 hour before** the class time.

Example:
- **Class**: Monday 4:30 PM
- **Booking opens**: previous Monday 3:30 PM
- **Cron job runs**: Monday 3:30 PM and books the class for 7 days from then

## Scheduler usage (cron)

### Preview what will be scheduled

```bash
python scheduler.py --dry-run
```

### Install cron jobs

```bash
python scheduler.py --install
```

### Remove cron jobs (only those created by this tool)

```bash
python scheduler.py --remove
```

### Inspect installed jobs

```bash
crontab -l
```

### Cron timing primer

Cron format: `minute hour day month day-of-week command`

Day-of-week numbers:
- `0` = Sunday
- `1` = Monday
- `2` = Tuesday
- `3` = Wednesday
- `4` = Thursday
- `5` = Friday
- `6` = Saturday

## Common commands

### Manual booking (bypass config)

```bash
source venv/bin/activate
python main.py "29-11-2025" "8:30 AM" "LF3 Strong" --user ryan
```

### Config-based booking (used by cron)

```bash
source venv/bin/activate
python book_from_config.py --date 2025-12-02
```

### Logs

All booking output is written to `logs/` (one file per day), for example:

```bash
tail -f logs/booking_monday.log
```

## Google Calendar integration (optional)

When a booking succeeds, the system can POST booking details to a per-user `calendar_webhook_url` (Google Apps Script Web App). This avoids Google Cloud OAuth setup.

### 1) Create a Google Apps Script web app

- Go to [script.google.com](https://script.google.com)
- Create a new project (e.g., “Altea Calendar Integration”)
- Replace the default code with the script below

```javascript
/**
 * Altea Calendar Integration
 *
 * This script receives booking data from the Altea auto-booker
 * and creates calendar events in your Google Calendar.
 */

function doPost(e) {
  try {
    const data = JSON.parse(e.postData.contents);

    const title = data.title || 'Fitness Class';
    const startTime = new Date(data.startTime);
    const endTime = new Date(data.endTime);
    const description = data.description || '';
    const location = data.location || 'Altea Active';

    const calendar = CalendarApp.getDefaultCalendar();
    const event = calendar.createEvent(title, startTime, endTime, {
      description: description,
      location: location
    });

    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        eventId: event.getId(),
        message: 'Event created successfully'
      }))
      .setMimeType(ContentService.MimeType.JSON);

  } catch (error) {
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Run manually once to authorize calendar permissions
function testCalendarAccess() {
  const calendar = CalendarApp.getDefaultCalendar();
  Logger.log('Calendar name: ' + calendar.getName());
  Logger.log('Calendar access verified!');
}
```

### 2) Deploy as a web app

- **Deploy** → **New deployment** → type: **Web app**
- **Execute as**: Me
- **Who has access**: Anyone
- Authorize access when prompted
- Copy the Web App URL (looks like `https://script.google.com/macros/s/.../exec`)

### 3) Add `calendar_webhook_url` to `users.yaml`

```yaml
users:
  ryan:
    altea_email: ryan@example.com
    altea_password: your-password
    notification_email: ryan@example.com
    calendar_webhook_url: https://script.google.com/macros/s/AKfycb...xyz/exec
```

### 4) Test the webhook

```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Class",
    "startTime": "2025-12-15T10:00:00",
    "endTime": "2025-12-15T11:00:00",
    "description": "Test event from Altea booker",
    "location": "Altea Active"
  }'
```

## Architecture (how it works)

```
┌─────────────────┐
│  classes.yaml   │  ← weekly schedule
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  scheduler.py   │  ← generates/installs cron jobs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    crontab      │  ← triggers at booking window open time
└────────┬────────┘
         │
         ▼
┌──────────────────────┐
│ book_from_config.py  │  ← chooses class + user for target date
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│      main.py         │  ← core booking via AlteaClient (Playwright)
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│   Altea website      │  ← books the class
└──────────────────────┘
```

## Notifications (optional)

Email notifications are sent on booking success/failure using Mailgun.

1) Copy `env.example` to `.env`:

```bash
cp env.example .env
```

2) Fill in:

```bash
MAILGUN_DOMAIN=your-mailgun-domain.mailgun.org
MAILGUN_API_KEY=key-your-api-key-here
FROM_EMAIL=altea-booking@your-domain.com
```

If Mailgun isn’t configured, booking still runs; you just won’t get emails.

## Troubleshooting

### Browser executable not found

```bash
source venv/bin/activate
playwright install chromium
```

### Permission denied: `./setup.sh`

```bash
chmod +x setup.sh
```

### Cron jobs not running

- Verify cron is running:
  - macOS: `ps aux | grep cron`
  - Linux: `service cron status`
- Check your crontab: `crontab -l`
- View recent cron activity:
  - macOS: `log show --predicate 'eventMessage contains "cron"' --last 1h`
  - Linux: `grep CRON /var/log/syslog`

### “No classes configured for [day]”

Normal if you don’t have a class for that weekday in `classes.yaml`.

### Email notifications not working

Booking will still proceed. Check:
- `.env` has correct Mailgun credentials
- Mailgun domain is verified
- Logs for Mailgun/API errors

### Calendar webhook “Authorization required”

In Apps Script:
- Run `testCalendarAccess` once and authorize
- Re-deploy the web app

## Security notes

- Never commit real `users.yaml` or `.env`.
- Treat `calendar_webhook_url` like a password (anyone with it can create events).

## License

For personal use only.
