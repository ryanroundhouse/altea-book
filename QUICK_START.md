# Quick Start Guide

Get your automatic fitness class booking up and running in 5 minutes.

## 1. Initial Setup (One Time)

```bash
# Run the setup script
./setup.sh

# Set up your user credentials
cp users.example.yaml users.yaml
nano users.yaml
```

Add your Altea credentials to `users.yaml`:
```yaml
users:
  ryan:
    altea_email: ryan@example.com
    altea_password: your-password-here
    notification_email: ryan@example.com
  
  katie:  # Add more users as needed
    altea_email: katie@example.com
    altea_password: her-password-here
    notification_email: katie@example.com
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
    user: ryan  # Must match a user in users.yaml
```

This means:
- **Class**: "LF3 Strong" on Mondays at 4:30 PM for ryan
- **Booking**: Automatically opens 7 days and 1 hour before (3:30 PM)
- **Result**: System will book automatically every Monday at 3:30 PM for the following Monday, using ryan's credentials

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
python main.py "29-11-2025" "8:30 AM" "LF3 Strong" --user ryan
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
  # Monday morning for ryan (books at 5:01 AM, 7 days before)
  - day: Monday
    time: "6:00 AM"
    name: "Hot Vinyasa"
    user: ryan
  
  # Monday afternoon for ryan (books at 3:31 PM, 7 days before)
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    user: ryan
  
  # Wednesday for katie (books at 11:31 AM, 7 days before)
  - day: Wednesday
    time: "12:30 PM"
    name: "Pilates"
    user: katie
  
  # Same class for both users (stagger times to avoid conflicts)
  - day: Friday
    time: "4:30 PM"
    name: "LF3 Strong"
    user: ryan
  
  - day: Friday
    time: "4:31 PM"  # Staggered by 1 minute
    name: "LF3 Strong"
    user: katie
```

**Note**: All classes automatically book 7 days and 1 hour before the class time. Each user's credentials from `users.yaml` are used for their bookings.

After editing, run:
```bash
python scheduler.py --install
```

Your cron will now handle all three classes automatically!

