#!/usr/bin/env python3
"""
Booking script that reads from the classes.yaml control file.
This script is meant to be called by cron jobs set up by the scheduler.
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import yaml
from dotenv import load_dotenv

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.client import AlteaClient
from src.notifications import EmailNotifier
from src.calendar import add_to_calendar

# Load environment variables
load_dotenv()


def load_config(config_path='classes.yaml'):
    """Load the classes configuration file."""
    config_file = project_root / config_path
    
    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}")
        sys.exit(1)
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def load_users(users_path='users.yaml'):
    """Load the users configuration file."""
    users_file = project_root / users_path
    
    if not users_file.exists():
        print(f"Error: Users configuration file not found: {users_file}")
        print("Copy users.example.yaml to users.yaml and configure your credentials.")
        sys.exit(1)
    
    with open(users_file, 'r') as f:
        users_config = yaml.safe_load(f)
    
    return users_config.get('users', {})


def get_user_credentials(users, user_name):
    """
    Get credentials for a specific user.
    
    Args:
        users: Dictionary of users from users.yaml
        user_name: Name of the user to look up
    
    Returns:
        Dictionary with altea_email, altea_password, notification_email
    """
    if user_name not in users:
        print(f"Error: User '{user_name}' not found in users.yaml")
        print(f"Available users: {', '.join(users.keys())}")
        sys.exit(1)
    
    user = users[user_name]
    
    required_fields = ['altea_email', 'altea_password', 'notification_email']
    for field in required_fields:
        if field not in user or not user[field]:
            print(f"Error: Missing '{field}' for user '{user_name}' in users.yaml")
            sys.exit(1)
    
    return user


def get_day_name(date_obj):
    """Get the day name (Monday, Tuesday, etc.) from a date object."""
    return date_obj.strftime('%A')


def find_class_for_date(config, target_date, time_filter=None, user_filter=None):
    """
    Find the class configuration for a given date.
    
    Args:
        config: The loaded YAML configuration
        target_date: datetime object for the target date
        time_filter: Optional time string to match (e.g., "4:30 PM")
        user_filter: Optional user name to match
    
    Returns:
        Class configuration dict or None if not found
    """
    day_name = get_day_name(target_date)
    
    for class_config in config.get('classes', []):
        if class_config['day'] != day_name:
            continue
        
        # If time filter specified, must match
        if time_filter and class_config.get('time') != time_filter:
            continue
        
        # If user filter specified, must match
        if user_filter and class_config.get('user') != user_filter:
            continue
        
        return class_config
    
    return None


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Book a class from the control file for a specific date',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Book class for today
  python book_from_config.py
  
  # Book class for a specific date
  python book_from_config.py --date 2025-11-25
  
  # Book class for next Monday
  python book_from_config.py --date 2025-12-02
        '''
    )
    
    parser.add_argument('--date',
                       help='Target date for the class (format: YYYY-MM-DD). Defaults to today.')
    parser.add_argument('--time',
                       help='Class time to book (e.g., "4:30 PM"). Required when multiple classes on same day.')
    parser.add_argument('--user',
                       help='User to book for (must match user in classes.yaml and users.yaml)')
    parser.add_argument('--config',
                       default='classes.yaml',
                       help='Path to the configuration file (default: classes.yaml)')
    parser.add_argument('--dry-run',
                       action='store_true',
                       help='Show what would be booked without actually booking')
    
    return parser.parse_args()


def main():
    args = parse_arguments()
    
    # Determine target date
    if args.date:
        try:
            target_date = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"Error: Invalid date format: {args.date}. Expected YYYY-MM-DD")
            sys.exit(1)
    else:
        target_date = datetime.now()
    
    # Load configuration
    config = load_config(args.config)
    
    # Find class for this date (with optional time/user filters from cron)
    class_config = find_class_for_date(config, target_date, args.time, args.user)
    
    if not class_config:
        day_name = get_day_name(target_date)
        filters = []
        if args.time:
            filters.append(f"time={args.time}")
        if args.user:
            filters.append(f"user={args.user}")
        filter_str = f" ({', '.join(filters)})" if filters else ""
        print(f"No class configured for {day_name} ({target_date.strftime('%Y-%m-%d')}){filter_str}")
        sys.exit(0)
    
    # Get user from class config
    user_name = class_config.get('user')
    if not user_name:
        print(f"Error: No 'user' specified for {class_config['day']} class in classes.yaml")
        sys.exit(1)
    
    # Load users and get credentials
    users = load_users()
    user_creds = get_user_credentials(users, user_name)
    
    # Format date for the booking script (DD-MM-YYYY)
    formatted_date = target_date.strftime('%d-%m-%Y')
    
    # Get settings
    settings = config.get('settings', {})
    headless = settings.get('headless', True)
    
    print(f"\n{'='*70}")
    print(f"BOOKING FROM CONFIG FILE")
    print(f"{'='*70}")
    print(f"Target Date: {formatted_date} ({get_day_name(target_date)})")
    print(f"Class Time: {class_config['time']}")
    print(f"Class Name: {class_config['name']}")
    print(f"User: {user_name}")
    print(f"Headless: {headless}")
    print(f"{'='*70}\n")
    
    if args.dry_run:
        print("DRY RUN - No booking will be made")
        return
    
    # Initialize email notifier
    try:
        notifier = EmailNotifier()
        print("✓ Email notifier initialized")
    except ValueError as e:
        print(f"⚠ Warning: Email notifications disabled - {e}")
        notifier = None
    
    # Book the class using the AlteaClient with user-specific credentials
    with AlteaClient(user_creds['altea_email'], user_creds['altea_password'], headless=headless) as client:
        # Step 1: Login
        if not client.login():
            print("Login failed, exiting.")
            sys.exit(1)
        
        # Step 2: Get schedule
        schedule = client.get_schedule(formatted_date)
        print(f"\n{'='*70}")
        print(f"Found {len(schedule)} classes on {formatted_date}")
        print(f"{'='*70}")
        
        # Step 3: Find the class
        matches = client.find_class(schedule, class_config['name'], class_config['time'])
        
        if matches:
            print(f"\n✓ Found {len(matches)} matching class(es)")
            
            for match in matches:
                print(f"\n  Title: {match['title']}")
                print(f"  Time: {match.get('time', 'N/A')}")
                print(f"  Spots Left: {match.get('spots_left', 'N/A')}")
                print(f"  Can Book: {match.get('can_book', False)}")
                
                class_info = {
                    'title': match['title'],
                    'date': formatted_date,
                    'time': match.get('time', 'N/A'),
                    'spots_left': match.get('spots_left', 'N/A'),
                    'url': match.get('url', '')
                }
                
                if match.get('can_book', False):
                    success = client.book_class(match['url'])
                    if success:
                        print("\n✓ Successfully booked class!")
                        
                        # Add to Google Calendar if webhook URL is configured
                        calendar_url = user_creds.get('calendar_webhook_url')
                        if calendar_url:
                            add_to_calendar(
                                webhook_url=calendar_url,
                                class_title=match['title'],
                                class_date=formatted_date,
                                class_time=match.get('time', class_config['time'])
                            )
                        
                        if notifier:
                            try:
                                notifier.send_booking_success(
                                    class_info,
                                    user_name=user_name,
                                    user_email=user_creds['notification_email']
                                )
                            except Exception as e:
                                print(f"Warning: Failed to send success email: {e}")
                    else:
                        print("\n✗ Failed to book class")
                        if notifier:
                            try:
                                notifier.send_booking_failure(
                                    class_info,
                                    "Failed to complete booking process.",
                                    user_name=user_name,
                                    user_email=user_creds['notification_email']
                                )
                            except Exception as e:
                                print(f"Warning: Failed to send failure email: {e}")
                else:
                    print("\n⚠ Class is full or not bookable")
                    if notifier:
                        try:
                            notifier.send_booking_failure(
                                class_info,
                                f"Class is full or not bookable. Spots left: {match.get('spots_left', 'Unknown')}",
                                user_name=user_name,
                                user_email=user_creds['notification_email']
                            )
                        except Exception as e:
                            print(f"Warning: Failed to send failure email: {e}")
        else:
            print(f"\n✗ No classes found matching '{class_config['name']}' at {class_config['time']}")
            if notifier:
                try:
                    class_info = {
                        'title': class_config['name'],
                        'date': formatted_date,
                        'time': class_config['time'],
                        'spots_left': 'N/A',
                        'url': ''
                    }
                    notifier.send_booking_failure(
                        class_info,
                        "Could not find the specified class in the schedule.",
                        user_name=user_name,
                        user_email=user_creds['notification_email']
                    )
                except Exception as e:
                    print(f"Warning: Failed to send failure email: {e}")


if __name__ == "__main__":
    main()
