import yaml
import sys
from src.client import AlteaClient

def load_config():
    try:
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config.yaml not found.")
        return None

def main():
    config = load_config()
    if not config:
        sys.exit(1)

    email = config['credentials']['email']
    password = config['credentials']['password']

    if password == "YOUR_PASSWORD_HERE":
        print("Please update config.yaml with your actual password.")
        sys.exit(1)

    # Use context manager to automatically handle browser lifecycle
    # Set headless=False for debugging, headless=True for production
    with AlteaClient(email, password, headless=False) as client:
        # Step 1: Login
        if not client.login():
            print("Login failed, exiting.")
            sys.exit(1)
        
        # Step 2: Get schedule for November 29, 2025
        target_date = "29-11-2025"
        schedule = client.get_schedule(target_date)
        
        # Print ALL classes found
        print(f"\n{'='*70}")
        print(f"ALL CLASSES FOUND ({len(schedule)} total):")
        print(f"{'='*70}")
        for i, cls in enumerate(schedule, 1):
            print(f"\n{i}. {cls['title']}")
            print(f"   Time: {cls.get('time', 'N/A')}")
            print(f"   URL: {cls.get('url', 'N/A')}")
            print(f"   Spots: {cls.get('spots_left', 'N/A')} | Full: {cls.get('is_full', False)}")
        
        # Step 3: Find the specific class: LF3 Strong at 12:30 PM
        print(f"\n{'='*70}")
        print("SEARCHING FOR: LF3 Strong at 12:30 PM")
        print(f"{'='*70}")
        
        matches = client.find_class(schedule, "LF3 Strong", "12:30 PM")

        if matches:
            print(f"\n✓ Found {len(matches)} matching class(es):")
            for match in matches:
                print(f"\n  Title: {match['title']}")
                print(f"  Time: {match.get('time', 'N/A')}")
                print(f"  Spots Left: {match.get('spots_left', 'N/A')}")
                print(f"  Can Book: {match.get('can_book', False)}")
                print(f"  URL: {match.get('url', 'N/A')}")
                
                # Book the class
                if match.get('can_book', False):
                    success = client.book_class(match['url'])
                    if success:
                        print("\n✓ Successfully initiated booking!")
                    else:
                        print("\n✗ Failed to book class")
                else:
                    print("\n⚠ Class is full or not bookable")
                    # Still navigate to see the page
                    client.page.goto("https://myaltea.app" + match['url'])
                    client.page.wait_for_load_state("networkidle")
                    client.page.screenshot(path="debug_class_page.png")
                    print("  Saved screenshot: debug_class_page.png")
        else:
            print(f"\n✗ No classes found matching 'LF3 Strong' at 12:30 PM")

if __name__ == "__main__":
    main()

