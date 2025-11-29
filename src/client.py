from playwright.sync_api import sync_playwright, Page, Browser
import time

class AlteaClient:
    def __init__(self, email: str, password: str, headless: bool = True):
        self.email = email
        self.password = password
        self.headless = headless
        self.browser = None
        self.page = None
        self.playwright = None

    def __enter__(self):
        """Context manager entry - starts browser"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=self.headless)
        self.page = self.browser.new_page()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - closes browser"""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def login(self):
        """
        Navigates to myaltea.app and logs in via the UI.
        """
        print(f"Logging in as {self.email}...")
        
        try:
            # Navigate to the site
            self.page.goto("https://myaltea.app")
            print("Loaded myaltea.app")
            
            # Wait for page to load
            self.page.wait_for_load_state("networkidle")
            
            # TODO: Find and click login button
            # We need to inspect the page to find the right selectors
            # For now, let's try common patterns
            
            # Look for login button/link
            # Common selectors: button with "Log in", "Sign in", etc.
            try:
                # Try to find login button
                login_button = self.page.locator("text=/log.*in/i").first
                if login_button.is_visible(timeout=5000):
                    print("Found login button, clicking...")
                    login_button.click()
                    self.page.wait_for_load_state("networkidle")
            except Exception as e:
                print(f"Could not find login button: {e}")
                print("Page might already show login form or we're already logged in")
            
            # Fill in email
            print("Looking for email input...")
            email_input = self.page.locator("input[type='email'], input[name='email'], input[placeholder*='email' i]").first
            email_input.fill(self.email)
            print("Filled email")
            
            # Fill in password
            print("Looking for password input...")
            password_input = self.page.locator("input[type='password']").first
            password_input.fill(self.password)
            print("Filled password")
            
            # Submit form
            print("Looking for submit button...")
            # The button text is "Sign-In" with an arrow
            submit_button = self.page.locator("button:has-text('Sign-In'), button:has-text('Sign In')").first
            
            # Click and wait for navigation
            print("Clicking submit button...")
            submit_button.click()
            
            # Wait for the page to navigate away from login
            # The site should redirect us after successful login
            print("Waiting for navigation after login...")
            time.sleep(3)  # Give it a moment for the authentication to process
            
            self.page.wait_for_load_state("networkidle")
            
            current_url = self.page.url
            print(f"Current URL after login: {current_url}")
            
            # Check if we see the "You must be logged in" message (means login failed)
            page_text = self.page.content()
            if "You must be logged in" in page_text:
                print("✗ Login failed - not authenticated")
                self.page.screenshot(path="debug_login_failed.png")
                return False
            
            # Check if we're still on a page with login form
            login_form_visible = self.page.locator("input[type='email']").count() > 0
            if login_form_visible:
                print("✗ Login failed - still see login form")
                self.page.screenshot(path="debug_login_failed.png")
                return False
            
            print("✓ Login successful!")
            return True
                
        except Exception as e:
            print(f"Login error: {e}")
            # Save screenshot for debugging
            self.page.screenshot(path="debug_login_error.png")
            print("Saved screenshot to debug_login_error.png")
            return False

    def get_schedule(self, date_str: str):
        """
        Navigates to the booking page for a specific date and extracts class data from the DOM.
        Date format: DD-MM-YYYY
        Returns a list of class dictionaries.
        """
        print(f"\nFetching schedule for {date_str}...")
        
        try:
            # Navigate to booking page with date
            url = f"https://myaltea.app/booking?date={date_str}"
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
            
            print(f"Loaded booking page: {self.page.url}")
            
            # Wait for initial classes to load
            print("Waiting for initial classes to load...")
            self.page.wait_for_timeout(3000)
            
            # Scroll down slowly to load all classes (virtual scrolling)
            # Collect classes as we go since virtual scrolling removes earlier items
            print("Scrolling to load all classes...")
            classes = []
            seen_urls = set()
            scroll_attempt = 0
            
            while scroll_attempt < 100:  # Safety limit
                # Get current scroll position
                scroll_height = self.page.evaluate("document.documentElement.scrollHeight")
                scroll_top = self.page.evaluate("document.documentElement.scrollTop")
                client_height = self.page.evaluate("document.documentElement.clientHeight")
                
                # Collect currently visible classes
                class_links = self.page.locator("a[href*='/booking/evt_']").all()
                
                for link in class_links:
                    try:
                        # Get the href
                        href = link.get_attribute("href")
                        
                        # Skip if we've already seen this class
                        if href in seen_urls:
                            continue
                        
                        seen_urls.add(href)
                        
                        # Get the class name
                        # Path: a/div/div[1]/div[2]/div[1]/span
                        name_element = link.locator("span.rt-Text.rt-r-size-4.rt-r-weight-bold").first
                        name = name_element.inner_text(timeout=1000) if name_element.count() > 0 else "Unknown"
                        
                        # Get the time
                        # Path: a/div/div[1]/div[2]/div[2]/div[1]/div/div/span[1]
                        time_element = link.locator("span.rt-Text.rt-r-size-2.rt-r-weight-bold").first
                        time = time_element.inner_text(timeout=1000) if time_element.count() > 0 else "Unknown"
                        
                        # Get all text to check for spots/full status
                        card_text = link.inner_text()
                        
                        # Extract spots left
                        import re
                        spots_match = re.search(r'Spots Left:\s*(\d+)', card_text, re.IGNORECASE)
                        spots_left = int(spots_match.group(1)) if spots_match else None
                        
                        # Check if full
                        is_full = "Full" in card_text or "Join Waitlist" in card_text
                        
                        class_info = {
                            'title': name.strip(),
                            'time': time.strip(),
                            'spots_left': spots_left,
                            'is_full': is_full,
                            'can_book': not is_full,
                            'url': href,
                        }
                        
                        classes.append(class_info)
                        
                        # Log each class
                        print(f"  {len(classes)}. {name} at {time} - URL: {href}")
                        
                    except Exception as e:
                        print(f"  Error parsing class: {e}")
                        continue
                
                # Check if we're at the bottom
                at_bottom = (scroll_top + client_height >= scroll_height - 10)
                
                if at_bottom:
                    print(f"  Reached bottom of page (scroll: {scroll_top + client_height}/{scroll_height})")
                    break
                
                # Scroll down
                self.page.evaluate("window.scrollBy(0, 400)")
                self.page.wait_for_timeout(300)
                    
                scroll_attempt += 1
            
            print(f"  Total scroll attempts: {scroll_attempt}")
            
            print(f"\nSuccessfully parsed {len(classes)} classes from DOM")
            
            return classes
            
        except Exception as e:
            print(f"Error fetching schedule: {e}")
            import traceback
            traceback.print_exc()
            self.page.screenshot(path="debug_schedule_error.png")
            print("Saved screenshot to debug_schedule_error.png")
            return []

    def find_class(self, schedule, class_name_partial: str, time_str: str):
        """
        Finds classes matching the partial name and time.
        Time format: "HH:MM AM/PM" or "HH:MM" (will try to match flexibly)
        Returns a list of matching classes.
        """
        matches = []
        
        # Normalize the search time
        search_time = time_str.strip().upper()
        
        for event in schedule:
            # Check if the class name matches (case-insensitive partial match)
            title = event.get('title', '')
            if class_name_partial.lower() in title.lower():
                # Check if the time matches
                event_time = event.get('time', '')
                
                if event_time:
                    # Normalize event time for comparison
                    normalized_event_time = event_time.strip().upper()
                    
                    # Try exact match first
                    if normalized_event_time == search_time:
                        matches.append(event)
                    # Also try matching just the time part (e.g., "8:30" matches "8:30 AM")
                    elif search_time in normalized_event_time or normalized_event_time in search_time:
                        matches.append(event)
        
        return matches
    
    def book_class(self, class_url: str, for_wife: bool = False):
        """
        Books a class by navigating to the class page and clicking the Book Now button.
        
        Args:
            class_url: The URL of the class (e.g., /booking/evt_xxx)
            for_wife: Whether to book for wife (if applicable)
        
        Returns:
            True if booking was successful, False otherwise
        """
        print(f"\nBooking class: {class_url}")
        
        try:
            # Navigate to the class page
            full_url = f"https://myaltea.app{class_url}"
            self.page.goto(full_url, timeout=60000)  # 60 second timeout for initial load
            # Use 'domcontentloaded' instead of 'networkidle' since the booking page
            # has continuous network activity (websockets, analytics) that prevents
            # it from ever reaching a truly idle state
            self.page.wait_for_load_state("domcontentloaded")
            
            print(f"Loaded class page: {self.page.url}")
            
            # Wait for the page to fully load
            self.page.wait_for_timeout(2000)
            
            # Try to find and click the "Book Now" button
            # First try using the XPath you provided
            try:
                print("Looking for Book Now button using XPath...")
                book_button = self.page.locator("xpath=/html/body/div[4]/div/div/div/button")
                
                if book_button.count() > 0:
                    print("Found button via XPath, clicking...")
                    book_button.click()
                    print("✓ Clicked Book Now button!")
                    
                    # Wait for confirmation dialog to appear
                    self.page.wait_for_timeout(2000)
                    
                    # Take a screenshot of the confirmation dialog
                    self.page.screenshot(path="debug_booking_confirmation.png")
                    print("Saved screenshot: debug_booking_confirmation.png")
                    
                    # Now click the "Confirm booking" button
                    print("Looking for Confirm booking button...")
                    confirm_button = self.page.locator("xpath=/html/body/div[5]/div/div[3]/div/button")
                    
                    if confirm_button.count() > 0:
                        print("Found Confirm booking button, clicking...")
                        confirm_button.click()
                        print("✓ Clicked Confirm booking button!")
                        
                        # Wait for booking to complete
                        self.page.wait_for_timeout(3000)
                        
                        # Take a screenshot of the final result
                        self.page.screenshot(path="debug_booking_result.png")
                        print("Saved screenshot: debug_booking_result.png")
                        
                        return True
                    else:
                        print("✗ Could not find Confirm booking button")
                        self.page.screenshot(path="debug_booking_error.png")
                        print("Saved screenshot: debug_booking_error.png")
                        return False
                else:
                    print("Button not found via XPath, trying text-based selector...")
                    # Try finding by text
                    book_button = self.page.locator("button:has-text('Book Now'), button:has-text('Book')")
                    
                    if book_button.count() > 0:
                        print("Found button via text, clicking...")
                        book_button.first.click()
                        print("✓ Clicked Book Now button!")
                        
                        # Wait for confirmation dialog to appear
                        self.page.wait_for_timeout(2000)
                        
                        # Take a screenshot of the confirmation dialog
                        self.page.screenshot(path="debug_booking_confirmation.png")
                        print("Saved screenshot: debug_booking_confirmation.png")
                        
                        # Now click the "Confirm booking" button
                        print("Looking for Confirm booking button...")
                        confirm_button = self.page.locator("xpath=/html/body/div[5]/div/div[3]/div/button")
                        
                        if confirm_button.count() > 0:
                            print("Found Confirm booking button, clicking...")
                            confirm_button.click()
                            print("✓ Clicked Confirm booking button!")
                            
                            # Wait for booking to complete
                            self.page.wait_for_timeout(3000)
                            
                            # Take a screenshot of the final result
                            self.page.screenshot(path="debug_booking_result.png")
                            print("Saved screenshot: debug_booking_result.png")
                            
                            return True
                        else:
                            print("✗ Could not find Confirm booking button")
                            self.page.screenshot(path="debug_booking_error.png")
                            print("Saved screenshot: debug_booking_error.png")
                            return False
                    else:
                        print("✗ Could not find Book Now button")
                        self.page.screenshot(path="debug_booking_error.png")
                        print("Saved screenshot: debug_booking_error.png")
                        return False
                        
            except Exception as e:
                print(f"Error clicking Book Now button: {e}")
                self.page.screenshot(path="debug_booking_error.png")
                print("Saved screenshot: debug_booking_error.png")
                return False
                
        except Exception as e:
            print(f"Error booking class: {e}")
            import traceback
            traceback.print_exc()
            self.page.screenshot(path="debug_booking_error.png")
            print("Saved screenshot: debug_booking_error.png")
            return False
