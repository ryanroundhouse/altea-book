#!/usr/bin/env python3
"""
Scheduler script to set up cron jobs for automatic class booking.

This script reads the classes.yaml configuration file and calculates when
booking windows open. It then generates cron job entries that can be installed
to automatically run the booking script at the right times.
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import subprocess


def load_config(config_path='classes.yaml'):
    """Load the classes configuration file."""
    config_file = Path(__file__).parent / config_path
    
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def parse_time(time_str):
    """Parse time string like '3:30 PM' and return hour and minute."""
    time_str = time_str.strip().upper()
    
    # Handle formats like "3:30 PM" or "03:30 PM"
    if 'AM' in time_str or 'PM' in time_str:
        time_part = time_str.replace('AM', '').replace('PM', '').strip()
        hour, minute = map(int, time_part.split(':'))
        
        if 'PM' in time_str and hour != 12:
            hour += 12
        elif 'AM' in time_str and hour == 12:
            hour = 0
        
        return hour, minute
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def calculate_booking_time(class_time_str):
    """
    Calculate booking time (1 hour before class time).
    
    Args:
        class_time_str: Class time string (e.g., "4:30 PM")
    
    Returns:
        Tuple of (hour, minute) for booking time in 24-hour format
    """
    hour, minute = parse_time(class_time_str)
    
    # Subtract 1 hour
    booking_hour = hour - 1
    
    # Handle wrap-around (e.g., 12:30 AM class -> 11:30 PM previous day)
    # Note: This would require the cron to run on the previous day,
    # which complicates things. For now, assume no classes start before 1 AM.
    if booking_hour < 0:
        raise ValueError(f"Class time {class_time_str} is too early (before 1:00 AM). "
                        "Booking would need to be the previous day, which is not supported.")
    
    return booking_hour, minute


def day_to_cron_day(day_name):
    """Convert day name to cron day number (0=Sunday, 1=Monday, etc.)."""
    days = {
        'Sunday': 0,
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6
    }
    return days.get(day_name)


def calculate_cron_day(class_day, days_before):
    """
    Calculate the cron day for when booking opens.
    
    Args:
        class_day: Day name of the class (e.g., "Monday")
        days_before: How many days before the class booking opens
    
    Returns:
        Cron day number (0-6, where 0=Sunday)
    """
    class_day_num = day_to_cron_day(class_day)
    booking_day_num = (class_day_num - days_before) % 7
    return booking_day_num


def generate_cron_entry(class_config, project_root, python_path, is_macos=True):
    """
    Generate a cron job entry for a class configuration.
    
    Booking rule: All classes open 7 days and 1 hour before the class time.
    
    Args:
        class_config: Class configuration from YAML
        project_root: Path to the project root directory
        python_path: Path to the Python interpreter to use
        is_macos: True for macOS, False for Linux
    
    Returns:
        Cron job string and class config
    """
    # Hardcoded rule: booking opens 7 days and 1 hour before
    days_before = 7
    
    # Calculate booking time (1 hour before class time)
    class_time = class_config['time']
    hour, minute = calculate_booking_time(class_time)
    
    # Calculate which day the cron should run (7 days before = same day of week)
    cron_day = calculate_cron_day(class_config['day'], days_before)
    
    # Path to the booking script
    script_path = project_root / 'book_from_config.py'
    
    # Calculate the target date (will be handled by the script)
    # Date command syntax differs between macOS and Linux
    if is_macos:
        # macOS: date -v+7d +%Y-%m-%d
        date_cmd = f'$(date -v+{days_before}d +\\%Y-\\%m-\\%d)'
    else:
        # Linux: date -d "+7 days" +%Y-%m-%d
        date_cmd = f'$(date -d "+{days_before} days" +\\%Y-\\%m-\\%d)'
    
    # Build the cron command
    # Format: minute hour * * day-of-week command
    cron_cmd = f'cd {project_root} && {python_path} {script_path} --date {date_cmd}'
    
    # Add log redirection
    log_file = project_root / 'logs' / f'booking_{class_config["day"].lower()}.log'
    cron_cmd += f' >> {log_file} 2>&1'
    
    cron_line = f'{minute} {hour} * * {cron_day} {cron_cmd}'
    
    return cron_line, class_config


def generate_crontab(config, project_root, python_path, is_macos=True):
    """Generate the full crontab content."""
    lines = []
    lines.append('# Altea Fitness Class Booking Cron Jobs')
    lines.append('# Generated by scheduler.py')
    lines.append(f'# Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    lines.append(f'# Platform: {"macOS" if is_macos else "Linux"}')
    lines.append('')
    
    # Add environment variables
    lines.append(f'SHELL=/bin/bash')
    lines.append(f'PATH=/usr/local/bin:/usr/bin:/bin')
    lines.append('')
    
    classes = config.get('classes', [])
    
    if not classes:
        print("Warning: No classes configured in classes.yaml")
        return None
    
    for class_config in classes:
        cron_line, cls = generate_cron_entry(class_config, project_root, python_path, is_macos)
        
        # Calculate booking time for display
        booking_hour, booking_minute = calculate_booking_time(cls['time'])
        booking_time_24h = f"{booking_hour:02d}:{booking_minute:02d}"
        
        # Add comment for readability
        lines.append(f'# {cls["day"]} {cls["time"]} - {cls["name"]}')
        lines.append(f'# Books 7 days in advance, 1 hour before class (at {booking_time_24h})')
        lines.append(cron_line)
        lines.append('')
    
    return '\n'.join(lines)


def get_current_crontab():
    """Get the current crontab content."""
    try:
        result = subprocess.run(['crontab', '-l'], 
                              capture_output=True, 
                              text=True,
                              check=False)
        if result.returncode == 0:
            return result.stdout
        else:
            # No crontab exists yet
            return ""
    except Exception as e:
        print(f"Error reading crontab: {e}")
        return ""


def install_crontab(new_crontab_content):
    """Install the new crontab."""
    try:
        # Write to temporary file
        temp_file = Path('/tmp/altea_crontab.tmp')
        with open(temp_file, 'w') as f:
            f.write(new_crontab_content)
        
        # Install the crontab
        result = subprocess.run(['crontab', str(temp_file)],
                              capture_output=True,
                              text=True,
                              check=True)
        
        # Clean up
        temp_file.unlink()
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing crontab: {e}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def merge_crontabs(existing, new, marker_start='# BEGIN ALTEA BOOKING', marker_end='# END ALTEA BOOKING'):
    """
    Merge new crontab entries with existing ones.
    
    Replaces content between markers if they exist, otherwise appends.
    """
    lines = existing.strip().split('\n') if existing.strip() else []
    
    # Remove old Altea booking section if it exists
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        if marker_start in line:
            start_idx = i
        if marker_end in line:
            end_idx = i
    
    if start_idx is not None and end_idx is not None:
        # Remove old section
        del lines[start_idx:end_idx+1]
    
    # Add new section
    if lines and lines[-1].strip():
        lines.append('')  # Add blank line before our section
    
    lines.append(marker_start)
    lines.append(new.strip())
    lines.append(marker_end)
    
    return '\n'.join(lines) + '\n'


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Set up cron jobs for automatic fitness class booking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Show what cron jobs would be created (dry run)
  python scheduler.py --dry-run
  
  # Install cron jobs
  python scheduler.py --install
  
  # Remove installed cron jobs
  python scheduler.py --remove
        '''
    )
    
    parser.add_argument('--config',
                       default='classes.yaml',
                       help='Path to configuration file (default: classes.yaml)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be scheduled without actually installing')
    parser.add_argument('--install',
                       action='store_true',
                       help='Install the cron jobs')
    parser.add_argument('--remove',
                       action='store_true',
                       help='Remove the Altea booking cron jobs')
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(__file__).parent.absolute()
    
    # Get Python path from virtual environment if available
    venv_python = project_root / 'venv' / 'bin' / 'python'
    if venv_python.exists():
        python_path = venv_python
    else:
        python_path = sys.executable
    
    # Detect OS for date command syntax
    is_macos = sys.platform == 'darwin'
    
    print(f"Project root: {project_root}")
    print(f"Python path: {python_path}")
    print(f"Platform: {'macOS' if is_macos else 'Linux'}")
    
    if args.remove:
        print("\nRemoving Altea booking cron jobs...")
        existing = get_current_crontab()
        
        # Remove section between markers
        lines = existing.strip().split('\n') if existing.strip() else []
        start_idx = None
        end_idx = None
        
        for i, line in enumerate(lines):
            if '# BEGIN ALTEA BOOKING' in line:
                start_idx = i
            if '# END ALTEA BOOKING' in line:
                end_idx = i
        
        if start_idx is not None and end_idx is not None:
            del lines[start_idx:end_idx+1]
            new_crontab = '\n'.join(lines).strip()
            
            if new_crontab:
                new_crontab += '\n'
            
            if install_crontab(new_crontab):
                print("✓ Successfully removed Altea booking cron jobs")
            else:
                print("✗ Failed to remove cron jobs")
        else:
            print("No Altea booking cron jobs found")
        
        return
    
    # Load configuration
    config = load_config(args.config)
    
    # Create logs directory if it doesn't exist
    logs_dir = project_root / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Generate crontab
    new_crontab = generate_crontab(config, project_root, python_path, is_macos)
    
    if not new_crontab:
        print("No cron jobs to generate")
        sys.exit(1)
    
    print("\n" + "="*70)
    print("GENERATED CRON JOBS")
    print("="*70)
    print(new_crontab)
    print("="*70)
    
    if args.dry_run:
        print("\nDRY RUN - No changes made to crontab")
        print("\nTo install these cron jobs, run:")
        print(f"  python {Path(__file__).name} --install")
        return
    
    if args.install:
        print("\nInstalling cron jobs...")
        
        # Get existing crontab
        existing = get_current_crontab()
        
        # Merge with existing crontab
        merged = merge_crontabs(existing, new_crontab)
        
        if install_crontab(merged):
            print("✓ Successfully installed cron jobs!")
            print("\nTo view your crontab, run: crontab -l")
            print("To edit your crontab, run: crontab -e")
            print(f"Logs will be saved to: {logs_dir}")
        else:
            print("✗ Failed to install cron jobs")
    else:
        print("\nTo install these cron jobs, run:")
        print(f"  python {Path(__file__).name} --install")


if __name__ == "__main__":
    main()

