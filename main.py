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
        
        # Step 3: Find the specific class: LF3 Strong at 8:30 AM
        print(f"\n{'='*70}")
        print("SEARCHING FOR: LF3 Strong at 8:30 AM")
        print(f"{'='*70}")
        
        matches = client.find_class(schedule, "LF3 Strong", "8:30 AM")
        
        if matches:
            print(f"\n✓ Found {len(matches)} matching class(es):")
            for match in matches:
                print(f"\n  Title: {match['title']}")
                print(f"  Time: {match.get('time', 'N/A')}")
                print(f"  Spots Left: {match.get('spots_left', 'N/A')}")
                print(f"  Can Book: {match.get('can_book', False)}")
                print(f"  URL: {match.get('url', 'N/A')}")
                
                # Navigate to the class page
                print(f"\n  Navigating to class page...")
                class_url = "https://myaltea.app" + match['url']
                client.page.goto(class_url)
                client.page.wait_for_load_state("networkidle")
                print(f"  ✓ Navigated to: {client.page.url}")
                
                # Take a screenshot
                client.page.screenshot(path="debug_class_page.png")
                print(f"  Saved screenshot: debug_class_page.png")
        else:
            print(f"\n✗ No classes found matching 'LF3 Strong' at 8:30 AM")

if __name__ == "__main__":
    main()

