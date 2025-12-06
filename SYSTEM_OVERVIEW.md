# System Overview

This document provides a high-level overview of the automatic booking system.

## Architecture

```
┌─────────────────┐
│  classes.yaml   │  ← You configure your weekly schedule here
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  scheduler.py   │  ← Reads config, generates and installs cron jobs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  crontab        │  ← System cron scheduler
└────────┬────────┘
         │
         │ (Triggers at booking window opening time)
         │
         ▼
┌──────────────────────┐
│ book_from_config.py  │  ← Reads config, calculates target date, books class
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  main.py logic       │  ← Core booking functionality (AlteaClient)
│  (AlteaClient)       │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  Altea website       │  ← Books the class
└──────────────────────┘
```

## File Structure

### Configuration Files
- **`classes.yaml`** - Weekly class schedule configuration
- **`users.yaml`** - User credentials (never commit this!)
- **`users.example.yaml`** - Template for users.yaml
- **`.env`** - Mailgun API keys (never commit this!)
- **`env.example`** - Template for .env file

### Core Scripts
- **`main.py`** - Original booking script (manual use)
- **`book_from_config.py`** - Config-based booking (called by cron)
- **`scheduler.py`** - Generates and installs cron jobs

### Library Files
- **`src/client.py`** - AlteaClient class (browser automation)
- **`src/notifications.py`** - Email notification system

### Documentation
- **`README.md`** - Full documentation
- **`QUICK_START.md`** - 5-minute setup guide
- **`SCHEDULING_GUIDE.md`** - Detailed scheduling documentation
- **`SYSTEM_OVERVIEW.md`** - This file
- **`design.md`** - Technical architecture details

### Setup & Config
- **`setup.sh`** - Automated setup script
- **`requirements.txt`** - Python dependencies

### Generated Files
- **`logs/`** - Booking logs (created automatically)
  - `booking_monday.log`
  - `booking_tuesday.log`
  - etc.

## How It Works

### 1. Configuration (`classes.yaml`)

You define your weekly schedule:

```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    user: ryan  # References a user defined in users.yaml
```

This means: "Book LF3 Strong every Monday at 4:30 PM for ryan." The system automatically calculates that booking opens 7 days and 1 hour before (3:30 PM) and uses ryan's credentials from `users.yaml`.

### 2. Scheduler (`scheduler.py`)

The scheduler:
1. Reads `classes.yaml`
2. Calculates when booking windows open (7 days and 1 hour before each class)
3. Generates cron job entries
4. Installs them into your system crontab

Example cron job generated:
```
30 15 * * 1 cd /path && python book_from_config.py --date $(date -v+7d +%Y-%m-%d) >> logs/booking_monday.log 2>&1
```

Translation:
- `30 15` = 3:30 PM
- `* * 1` = Every Monday
- `date -v+7d` = Calculate date 7 days from now
- `>> logs/booking_monday.log` = Save output to log file

### 3. Automatic Execution (Cron)

Every Monday at 3:30 PM, cron automatically:
1. Runs `book_from_config.py`
2. Passes the target date (7 days from now)
3. Logs output to `logs/booking_monday.log`

### 4. Config-Based Booking (`book_from_config.py`)

This script:
1. Receives the target date from cron
2. Reads `classes.yaml` to find what class to book
3. Looks up user credentials from `users.yaml`
4. Logs in as that user and books the class
5. Sends email notifications to the user

### 5. Core Booking (`main.py` / `AlteaClient`)

The AlteaClient:
1. Launches headless browser (Playwright)
2. Logs into Altea website
3. Navigates to schedule page
4. Finds the specified class
5. Books it
6. Takes screenshots for debugging

### 6. Notifications (`src/notifications.py`)

The EmailNotifier:
1. Sends success/failure emails via Mailgun
2. Includes class details, spots left, etc.
3. Sends to the user's notification email (from `users.yaml`)

## Data Flow Example

Let's trace a booking for "LF3 Strong" on Monday, December 9, 2025:

**Today: Monday, December 2, 2025, 3:30 PM**

1. **Cron triggers** at 3:30 PM (scheduled by scheduler.py)

2. **Calculates target date**:
   ```bash
   date -v+7d  # Returns: 2025-12-09
   ```

3. **Runs booking script**:
   ```bash
   python book_from_config.py --date 2025-12-09
   ```

4. **Script reads config**:
   - Finds: Monday = "LF3 Strong" at 4:30 PM
   - user = ryan
   - Loads ryan's credentials from `users.yaml`

5. **Launches browser** (headless):
   - Login to Altea as ryan
   - Navigate to schedule for 2025-12-09
   - Find "LF3 Strong" at 4:30 PM
   - Click "Book" button

6. **Sends email to ryan**:
   - ✅ Success! Booked "LF3 Strong" for Dec 9 at 4:30 PM
   - Spots left: 5
   - Date: 09-12-2025

7. **Logs everything**:
   ```
   logs/booking_monday.log:
   [2025-12-02 15:30:15] Booking from config...
   [2025-12-02 15:30:18] Found 12 classes on 09-12-2025
   [2025-12-02 15:30:19] ✓ Found matching class: LF3 Strong
   [2025-12-02 15:30:22] ✓ Successfully booked class!
   ```

## Key Features

### 🔄 Recurring Weekly Bookings
- Define once, runs forever
- Each day can have multiple classes
- Multiple users supported (each with their own credentials)

### 🤖 Fully Automated
- No manual intervention needed
- Runs in headless mode (no GUI)
- Cron handles scheduling

### 📧 Email Notifications
- Success confirmations
- Failure alerts with details
- Separate emails for wife bookings

### 🐧 Cross-Platform
- macOS support (Darwin)
- Linux support (Ubuntu, Debian, etc.)
- Automatic OS detection for date commands

### 📝 Comprehensive Logging
- Separate log file per day
- All output captured (stdout + stderr)
- Easy debugging with timestamps

### 🔒 Secure
- Credentials in .env (never committed)
- .gitignore protects sensitive files
- Local execution only

## Maintenance

### Updating Your Schedule

1. Edit `classes.yaml`
2. Run `python scheduler.py --install`
3. Done! Cron jobs are updated

### Checking Status

```bash
# View installed cron jobs
crontab -l

# View recent booking activity
tail -50 logs/booking_monday.log

# Test configuration
python scheduler.py --dry-run
```

### Troubleshooting

```bash
# Test booking manually
source venv/bin/activate
python book_from_config.py --date 2025-12-09 --dry-run

# Check logs
ls -lh logs/

# Verify cron is running
ps aux | grep cron  # macOS/Linux
```

## Extending the System

### Add New Class

Edit `classes.yaml`:
```yaml
classes:
  # ... existing classes ...
  
  - day: Saturday
    time: "9:00 AM"
    name: "Bootcamp"
    user: ryan
```

Then: `python scheduler.py --install`

The system will automatically book it 7 days and 1 hour before (Saturday at 8:00 AM).

### Add New User

Edit `users.yaml`:
```yaml
users:
  # ... existing users ...
  
  marcus:
    altea_email: marcus@example.com
    altea_password: secret123
    notification_email: marcus@example.com
```

Then reference them in `classes.yaml` with `user: marcus`.

### Different Booking Times

The booking rule (7 days and 1 hour before) is hardcoded for all classes. If you need different timing, you would need to modify the `calculate_booking_time()` function in `scheduler.py`.

### Book Same Class for Multiple Users

Add separate entries for each user with slightly different times:
```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    user: ryan  # Books for ryan at 3:31 PM
  
  - day: Monday
    time: "4:31 PM"  # Stagger by 1 min to space cron jobs
    name: "LF3 Strong"
    user: katie  # Books for katie at 3:32 PM
```

**Note**: Staggering the class time by 1 minute spaces the bookings apart to avoid race conditions.

## Best Practices

1. **Test first**: Always use `--dry-run` when testing
2. **Check logs**: Review logs after first few bookings
3. **Monitor emails**: Ensure notifications are working
4. **Backup config**: Keep a copy of your `classes.yaml`
5. **Update regularly**: Keep dependencies updated with `pip install -r requirements.txt --upgrade`

## Quick Reference

| Task | Command |
|------|---------|
| Preview schedule | `python scheduler.py --dry-run` |
| Install cron jobs | `python scheduler.py --install` |
| Remove cron jobs | `python scheduler.py --remove` |
| View cron jobs | `crontab -l` |
| Test booking | `python book_from_config.py --date YYYY-MM-DD --dry-run` |
| Manual booking | `python main.py "DD-MM-YYYY" "HH:MM AM/PM" "Class Name" --user ryan` |
| View logs | `tail -f logs/booking_*.log` |
| Check config | `cat classes.yaml` |

## Support Files

For more details, see:
- **Setup**: `QUICK_START.md`
- **Scheduling**: `SCHEDULING_GUIDE.md`
- **Full docs**: `README.md`
- **Technical**: `design.md`

