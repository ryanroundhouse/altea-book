# Quick Start Guide

Get your automatic fitness class booking up and running in 5 minutes.

## 1. Initial Setup (One Time)

```bash
# Run the setup script
./setup.sh

# Edit your credentials
nano .env
```

Add your Altea credentials to `.env`:
```
ALTEA_EMAIL=your-email@example.com
ALTEA_PASSWORD=your-password-here
```

## 2. Configure Your Classes

Edit `classes.yaml` to define your weekly schedule:

```bash
nano classes.yaml
```

Example configuration:

```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    for_wife: false
```

This means:
- **Class**: "LF3 Strong" on Mondays at 4:30 PM
- **Booking**: Automatically opens 7 days and 1 hour before (3:30 PM)
- **Result**: System will book automatically every Monday at 3:30 PM for the following Monday

## 3. Test Your Configuration

```bash
# Activate virtual environment
source venv/bin/activate

# Preview what would be scheduled
python scheduler.py --dry-run

# Test booking for next Monday (without actually booking)
python book_from_config.py --date 2025-12-02 --dry-run
```

## 4. Install Automatic Scheduling

```bash
python scheduler.py --install
```

Done! Your classes will now be booked automatically. 🎉

## Common Commands

### View scheduled cron jobs
```bash
crontab -l
```

### Check booking logs
```bash
tail -f logs/booking_monday.log
```

### Manual booking (bypass config)
```bash
python main.py "29-11-2025" "8:30 AM" "LF3 Strong"
```

### Update your schedule
1. Edit `classes.yaml`
2. Run `python scheduler.py --install` (updates existing jobs)

### Remove automatic scheduling
```bash
python scheduler.py --remove
```

## Troubleshooting

### Test if everything works
```bash
source venv/bin/activate
python book_from_config.py --date 2025-12-02 --dry-run
```

### Check cron is running
```bash
# macOS
ps aux | grep cron

# Linux
service cron status
```

### View recent cron activity (macOS)
```bash
log show --predicate 'eventMessage contains "cron"' --last 1h
```

### View recent cron activity (Linux)
```bash
grep CRON /var/log/syslog
```

## Need More Help?

- **Detailed scheduling guide**: See `SCHEDULING_GUIDE.md`
- **Architecture details**: See `design.md`
- **Full documentation**: See `README.md`

## Example: Adding Multiple Classes

```yaml
classes:
  # Monday morning (books at 5:00 AM, 7 days before)
  - day: Monday
    time: "6:00 AM"
    name: "Hot Vinyasa"
    for_wife: false
  
  # Monday afternoon (books at 3:30 PM, 7 days before)
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    for_wife: false
  
  # Wednesday for wife (books at 11:30 AM, 7 days before)
  - day: Wednesday
    time: "12:30 PM"
    name: "Pilates"
    for_wife: true
```

**Note**: All classes automatically book 7 days and 1 hour before the class time.

After editing, run:
```bash
python scheduler.py --install
```

Your cron will now handle all three classes automatically!

