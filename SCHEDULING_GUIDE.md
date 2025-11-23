# Scheduling Guide

This guide explains how to set up automatic booking for your recurring weekly fitness classes.

## Quick Start

1. Edit `classes.yaml` to define your weekly classes
2. Run `python scheduler.py --dry-run` to preview
3. Run `python scheduler.py --install` to activate
4. Done! Your classes will be booked automatically

## Understanding the Configuration

### Class Configuration

Each class entry in `classes.yaml` has these fields:

```yaml
- day: Monday              # Day of the week for the class
  time: "4:30 PM"          # Time of the class
  name: "LF3 Strong"       # Class name (partial match works)
  for_wife: false          # true = book for wife, false = book for you
```

**Booking Window**: All classes automatically open for booking **7 days and 1 hour before** the class time. For example:
- Class at Monday 4:30 PM → Books on Monday 3:30 PM (7 days before)
- Class at Tuesday 6:00 AM → Books on Tuesday 5:00 AM (7 days before)

### How Booking Windows Work

All fitness classes open for booking **7 days and 1 hour before** the class time. For example:

- **Your class**: Monday, December 9 at 4:30 PM
- **Booking opens**: Monday, December 2 at 3:30 PM (7 days and 1 hour before)
- **The system**: Automatically books on Dec 2 at 3:30 PM

### Multiple Classes

You can configure multiple classes for different days:

```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    for_wife: false
  
  - day: Wednesday
    time: "6:00 AM"
    name: "Hot Vinyasa"
    for_wife: false
  
  - day: Friday
    time: "12:30 PM"
    name: "Pilates"
    for_wife: true
```

All classes automatically book 7 days and 1 hour before the class time.

## Scheduler Commands

### Preview what will be scheduled

```bash
python scheduler.py --dry-run
```

This shows you:
- Which cron jobs would be created
- When they will run
- What they will book

Example output:
```
# Monday 4:30 PM - LF3 Strong
# Books 7 days in advance, 1 hour before class (at 15:30)
30 15 * * 1 cd /Users/you/altea-book && .../python book_from_config.py --date $(date -v+7d +%Y-%m-%d)
```

Translation: Every Monday (`* * 1`) at 15:30 (3:30 PM), run the booking script to book a class 7 days from now.

### Install the cron jobs

```bash
python scheduler.py --install
```

This will:
1. Read your existing crontab (if any)
2. Add/update the Altea booking jobs
3. Keep any other existing cron jobs intact

### Remove the cron jobs

```bash
python scheduler.py --remove
```

This removes only the Altea booking cron jobs and keeps everything else.

### View active cron jobs

```bash
crontab -l
```

Shows all your active cron jobs, including the Altea booking ones.

## Understanding Cron Timing

Cron uses this format: `minute hour day month day-of-week command`

Examples:
- `30 15 * * 1` = Every Monday at 3:30 PM
- `0 6 * * 2` = Every Tuesday at 6:00 AM
- `30 11 * * 3` = Every Wednesday at 11:30 AM

Day of week numbers:
- 0 = Sunday
- 1 = Monday
- 2 = Tuesday
- 3 = Wednesday
- 4 = Thursday
- 5 = Friday
- 6 = Saturday

## Manual Booking

### Book from configuration

```bash
# Book class for a specific date
python book_from_config.py --date 2025-12-02

# Test without actually booking
python book_from_config.py --date 2025-12-02 --dry-run
```

### Direct booking (without config)

```bash
python main.py "02-12-2025" "4:30 PM" "LF3 Strong"
```

## Logs

All booking activity is logged to the `logs/` directory:

```bash
# View Monday booking logs
tail -f logs/booking_monday.log

# View all logs
ls -l logs/
```

Log files are named: `booking_<day>.log` (e.g., `booking_monday.log`)

## Troubleshooting

### "No classes configured for [day]"

This is normal if you don't have a class configured for that day. The script will exit quietly.

### Cron jobs not running

1. Check if cron is running: `ps aux | grep cron`
2. View cron logs (macOS): `log show --predicate 'eventMessage contains "cron"' --last 1h`
3. View cron logs (Linux): `grep CRON /var/log/syslog`
4. Check your crontab: `crontab -l`

### Test a booking manually

```bash
# Activate the virtual environment
source venv/bin/activate

# Test booking for next Monday
python book_from_config.py --date $(date -v+7d +%Y-%m-%d) --dry-run
```

### Email notifications not working

The script will still book classes even if email notifications fail. Check:
1. Your `.env` file has correct Mailgun credentials
2. The Mailgun domain is verified
3. Check logs for email-related errors

## Tips

### Same class multiple times per week

If you want the same class on multiple days:

```yaml
classes:
  - day: Monday
    time: "6:00 AM"
    name: "Hot Vinyasa"
    booking_window:
      days_before: 7
      time: "5:00 AM"
  
  - day: Friday
    time: "6:00 AM"
    name: "Hot Vinyasa"
    booking_window:
      days_before: 7
      time: "5:00 AM"
```

### Testing without disrupting cron

Use `--dry-run` to test changes to `classes.yaml`:

```bash
python scheduler.py --dry-run
```

### Updating your schedule

1. Edit `classes.yaml`
2. Run `python scheduler.py --install` (it will update existing jobs)

### Booking for your wife

Set `for_wife: true` in the class configuration. If configured, emails will be sent to both you and your wife.

## Advanced: Understanding the Date Calculation

The cron job runs on the booking day and calculates the target date:

```bash
# On Monday, Dec 2 at 3:30 PM, this calculates Dec 9
date -v+7d +%Y-%m-%d
```

The booking script receives this calculated date and books the class for that day.

## Support

For issues or questions:
1. Check the logs: `tail -f logs/booking_*.log`
2. Test manually: `python book_from_config.py --date YYYY-MM-DD --dry-run`
3. Review your configuration: `cat classes.yaml`

