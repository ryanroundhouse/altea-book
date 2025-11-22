# Gym Booking Bot Design Document

## 1. Overview
This project aims to automate the process of booking gym classes at Altea Active. The system will run on a Linux server and automatically book specific classes for the primary user and/or their partner as soon as the booking window opens.

## 2. Requirements
*   **Users**: Primary account holder + associated partner account.
*   **Selection**: Bookings are based on Class Name, Date, and Time.
*   **Timing**: Booking window opens **1 week + 1 hour** before the class start time.
*   **Platform**: Python script executed via Cron on a Linux server.
*   **Notifications**:
    *   Primary User bookings: Email to Primary.
    *   Partner bookings: Email to Primary + Partner.
    *   Triggers: On both success and failure.

## 3. Architecture

### 3.1 Tech Stack
*   **Language**: Python 3.x
*   **Dependencies**: 
    *   `playwright` (browser automation - handles auth automatically)
    *   `pyyaml` (config parsing)
    *   `smtplib` (standard library for emails)
*   **Scheduling**: System `cron` to trigger the script at specific times.
*   **Browser**: Chromium (headless) - runs without display on Linux servers.

### 3.2 Components

1.  **Configuration Manager**:
    *   Reads a `config.yaml` (or JSON) file containing:
        *   Credentials (email/password/API keys).
        *   User profiles (Mapping names to internal IDs).
        *   Target Classes (The "Wishlist").
        *   SMTP settings.

2.  **Altea Client (`AlteaClient`)**:
    *   Uses Playwright to automate browser interactions.
    *   Handles authentication via the web UI (browser manages all cookies/tokens).
    *   Methods:
        *   `login()`: Navigates to login page and authenticates.
        *   `get_schedule(date)`: Navigates to booking page and extracts class data.
        *   `book_class(class_id)`: Clicks through the booking flow.

3.  **Booking Logic (`Booker`)**:
    *   Calculates the target window.
    *   Orchestrates the flow: Auth -> Search -> Book -> Notify.
    *   Handles retry logic for transient failures.

4.  **Notifier**:
    *   Simple SMTP wrapper to send HTML/Text emails.
    *   Logic to determine recipients based on who the booking was for.

## 4. Data Flow (Happy Path)

1.  **Cron Trigger**: Script starts (e.g., `python main.py --target "Yoga"` or checks all pending targets).
2.  **Auth**: Script logs in using the provided curl equivalent (Firebase Auth).
3.  **Discovery**: Script queries the schedule for the target date/time.
    *   *Challenge*: We need to map "Tuesday at 6 PM" to a specific `scheduleId` or `classId` dynamic to that week.
4.  **Booking**: Script sends a POST request to the booking endpoint with the User IDs.
5.  **Notification**: Success email sent to relevant parties.

## 5. Configuration Draft (`config.yaml`)

```yaml
credentials:
  email: "rg@ryangraham.ca"
  password: "..."

notification:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  username: "..."
  password: "..."
  primary_email: "rg@ryangraham.ca"
  partner_email: "wife@example.com"

# We need to discover the internal IDs for users
users:
  ryan: "user_id_1"
  wife: "user_id_2"

# The classes we want to book
targets:
  - name: "Hot Yoga"
    day_of_week: "Tuesday"
    time: "18:00"
    attendees: ["ryan", "wife"]
  - name: "Spin"
    day_of_week: "Thursday"
    time: "07:00"
    attendees: ["ryan"]
```

## 6. Unknowns & Next Steps (Reverse Engineering)

### 6.1 Approach: Browser Automation
*   **Why Playwright**: The authentication system uses signed JWTs that we cannot forge. Browser automation handles all cookies/tokens automatically.
*   **UI Flow**:
    1.  Navigate to `https://myaltea.app`
    2.  Click "Login" button
    3.  Fill in email/password
    4.  Submit form (browser handles Firebase auth + cookie setting)
    5.  Navigate to booking page for target date
    6.  Find the target class by name/time
    7.  Click "Book" button
    8.  Confirm booking
    9.  Verify success

### 6.2 Selectors (to be determined during implementation)
*   Login button: TBD
*   Email input: TBD
*   Password input: TBD
*   Submit button: TBD
*   Class cards: TBD
*   Book button: TBD

### Action Plan
1.  ✓ Switch to Playwright architecture
2.  Implement browser-based `AlteaClient`
3.  Test login flow
4.  Test booking flow
5.  Add error handling and notifications

