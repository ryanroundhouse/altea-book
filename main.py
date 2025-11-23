import sys
import os
import argparse
from datetime import datetime
from dotenv import load_dotenv
from src.client import AlteaClient
from src.notifications import EmailNotifier

# Load environment variables from .env file
load_dotenv()

def parse_arguments():
    """Parse and validate command line arguments."""
    parser = argparse.ArgumentParser(
        description='Altea Active Gym Class Booking Bot',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Book LF3 Strong class at 8:30 AM on November 29, 2025
  python main.py "29-11-2025" "8:30 AM" "LF3 Strong"
  
  # Book Hot Vinyasa at 7:30 AM on December 1, 2025
  python main.py "01-12-2025" "7:30 AM" "Hot Vinyasa"
  
  # Book any class with partial name match
  python main.py "15-12-2025" "12:30 PM" "Pilates"

Date Format: DD-MM-YYYY (e.g., 29-11-2025)
Time Format: HH:MM AM/PM (e.g., 8:30 AM, 12:30 PM)
Class Name: Partial match, case-insensitive (e.g., "LF3", "Strong", "Vinyasa")
        '''
    )
    
    parser.add_argument('date', 
                       help='Date of the class (format: DD-MM-YYYY)')
    parser.add_argument('time', 
                       help='Time of the class (format: HH:MM AM/PM)')
    parser.add_argument('class_name', 
                       help='Name of the class (partial match)')
    parser.add_argument('--for-wife', 
                       action='store_true',
                       help='Book for wife instead of yourself')
    parser.add_argument('--headless',
                       action='store_true',
                       default=False,
                       help='Run browser in headless mode (no GUI)')
    
    args = parser.parse_args()
    
    # Validate date format
    try:
        datetime.strptime(args.date, '%d-%m-%Y')
    except ValueError:
        parser.error(f"Invalid date format: {args.date}. Expected DD-MM-YYYY (e.g., 29-11-2025)")
    
    # Validate time format (basic check)
    time_upper = args.time.upper()
    if not ('AM' in time_upper or 'PM' in time_upper):
        parser.error(f"Invalid time format: {args.time}. Expected HH:MM AM/PM (e.g., 8:30 AM)")
    
    return args

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Load credentials from environment variables
    email = os.getenv('ALTEA_EMAIL')
    password = os.getenv('ALTEA_PASSWORD')
    
    if not email or not password:
        print("Error: ALTEA_EMAIL and ALTEA_PASSWORD must be set in .env file")
        print("Copy env.example to .env and configure your credentials.")
        sys.exit(1)

    # Initialize email notifier
    try:
        notifier = EmailNotifier()
        print("✓ Email notifier initialized")
    except ValueError as e:
        print(f"⚠ Warning: Email notifications disabled - {e}")
        notifier = None
    
    # Print booking details
    print(f"\n{'='*70}")
    print(f"ALTEA BOOKING BOT")
    print(f"{'='*70}")
    print(f"Date: {args.date}")
    print(f"Time: {args.time}")
    print(f"Class: {args.class_name}")
    print(f"Booking for: {'Wife' if args.for_wife else 'You'}")
    print(f"{'='*70}\n")
    
    # Use context manager to automatically handle browser lifecycle
    with AlteaClient(email, password, headless=args.headless) as client:
        # Step 1: Login
        if not client.login():
            print("Login failed, exiting.")
            sys.exit(1)
        
        # Step 2: Get schedule for the specified date
        schedule = client.get_schedule(args.date)
        
        print(f"\n{'='*70}")
        print(f"Found {len(schedule)} classes on {args.date}")
        print(f"{'='*70}")
        
        # Step 3: Find the specific class
        print(f"\n{'='*70}")
        print(f"SEARCHING FOR: {args.class_name} at {args.time}")
        print(f"{'='*70}")
        
        matches = client.find_class(schedule, args.class_name, args.time)

        if matches:
            print(f"\n✓ Found {len(matches)} matching class(es):")
            for match in matches:
                print(f"\n  Title: {match['title']}")
                print(f"  Time: {match.get('time', 'N/A')}")
                print(f"  Spots Left: {match.get('spots_left', 'N/A')}")
                print(f"  Can Book: {match.get('can_book', False)}")
                print(f"  URL: {match.get('url', 'N/A')}")
                
                # Prepare class info for email notification
                class_info = {
                    'title': match['title'],
                    'date': args.date,
                    'time': match.get('time', 'N/A'),
                    'spots_left': match.get('spots_left', 'N/A'),
                    'url': match.get('url', '')
                }
                
                # Book the class
                if match.get('can_book', False):
                    success = client.book_class(match['url'])
                    if success:
                        print("\n✓ Successfully initiated booking!")
                        
                        # Send success notification
                        if notifier:
                            try:
                                notifier.send_booking_success(class_info, for_wife=args.for_wife)
                            except Exception as e:
                                print(f"Warning: Failed to send success email: {e}")
                    else:
                        print("\n✗ Failed to book class")
                        
                        # Send failure notification
                        if notifier:
                            try:
                                notifier.send_booking_failure(
                                    class_info, 
                                    "Failed to complete booking process. The booking button may not have been found or clicked.",
                                    for_wife=args.for_wife
                                )
                            except Exception as e:
                                print(f"Warning: Failed to send failure email: {e}")
                else:
                    print("\n⚠ Class is full or not bookable")
                    
                    # Send failure notification
                    if notifier:
                        try:
                            notifier.send_booking_failure(
                                class_info,
                                f"Class is full or not bookable. Spots left: {match.get('spots_left', 'Unknown')}",
                                for_wife=args.for_wife
                            )
                        except Exception as e:
                            print(f"Warning: Failed to send failure email: {e}")
                    
                    # Still navigate to see the page
                    client.page.goto("https://myaltea.app" + match['url'])
                    client.page.wait_for_load_state("networkidle")
                    client.page.screenshot(path="debug_class_page.png")
                    print("  Saved screenshot: debug_class_page.png")
        else:
            print(f"\n✗ No classes found matching '{args.class_name}' at {args.time}")
            
            # Send failure notification if no matching class found
            if notifier:
                try:
                    class_info = {
                        'title': args.class_name,
                        'date': args.date,
                        'time': args.time,
                        'spots_left': 'N/A',
                        'url': ''
                    }
                    notifier.send_booking_failure(
                        class_info,
                        "Could not find the specified class in the schedule. It may not be available on this date.",
                        for_wife=args.for_wife
                    )
                except Exception as e:
                    print(f"Warning: Failed to send failure email: {e}")

if __name__ == "__main__":
    main()

