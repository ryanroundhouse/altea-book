"""
Google Calendar integration via Google Apps Script webhook.

This module sends booking details to a user's deployed Google Apps Script,
which then creates a calendar event in their Google Calendar.
"""

import requests
from datetime import datetime, timedelta


def parse_class_time(time_str: str) -> tuple[int, int]:
    """
    Parse a time string like '3:30 PM' into hour and minute (24-hour format).
    
    Args:
        time_str: Time string (e.g., "3:30 PM", "10:00 AM")
    
    Returns:
        Tuple of (hour, minute) in 24-hour format
    """
    time_str = time_str.strip().upper()
    
    if 'AM' in time_str or 'PM' in time_str:
        time_part = time_str.replace('AM', '').replace('PM', '').strip()
        hour, minute = map(int, time_part.split(':'))
        
        if 'PM' in time_str and hour != 12:
            hour += 12
        elif 'AM' in time_str and hour == 12:
            hour = 0
        
        return hour, minute
    else:
        # Try parsing as 24-hour format
        parts = time_str.split(':')
        return int(parts[0]), int(parts[1]) if len(parts) > 1 else 0


def add_to_calendar(
    webhook_url: str,
    class_title: str,
    class_date: str,
    class_time: str,
    duration_minutes: int = 60
) -> bool:
    """
    Add a booked class to Google Calendar via Apps Script webhook.
    
    Args:
        webhook_url: The deployed Google Apps Script web app URL
        class_title: Name of the class (e.g., "Strength and Conditioning")
        class_date: Date string in DD-MM-YYYY format
        class_time: Time string (e.g., "4:30 PM")
        duration_minutes: Class duration in minutes (default 60)
    
    Returns:
        True if the calendar event was created successfully, False otherwise
    """
    if not webhook_url:
        print("⚠ No calendar webhook URL configured, skipping calendar integration")
        return False
    
    try:
        # Parse the date (DD-MM-YYYY format from Altea)
        day, month, year = map(int, class_date.split('-'))
        
        # Parse the time
        hour, minute = parse_class_time(class_time)
        
        # Build start datetime
        start_dt = datetime(year, month, day, hour, minute)
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Format for the Apps Script (ISO 8601)
        payload = {
            'title': f"🏋️ {class_title}",
            'startTime': start_dt.isoformat(),
            'endTime': end_dt.isoformat(),
            'description': f"Booked via Altea Auto-Booker\nClass: {class_title}\nDate: {class_date}\nTime: {class_time}",
            'location': 'Altea Active, 1660 Carling Ave, Ottawa, ON K2A 1C4'
        }
        
        print(f"📅 Adding to calendar: {class_title} on {class_date} at {class_time}")
        
        # Send to the Apps Script webhook
        response = requests.post(
            webhook_url,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json() if response.text else {}
            if result.get('success', True):  # Default to success if no JSON response
                print("✓ Calendar event created successfully")
                return True
            else:
                print(f"✗ Calendar API returned error: {result.get('error', 'Unknown error')}")
                return False
        else:
            print(f"✗ Calendar webhook returned status {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("✗ Calendar webhook timed out")
        return False
    except requests.exceptions.RequestException as e:
        print(f"✗ Calendar webhook request failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Error adding to calendar: {e}")
        return False

