# Gym Booking Bot Design Document

## 1. Overview
This project aims to automate the process of booking gym classes at Altea Active. The system will run on a Linux server and automatically book specific classes for the primary user and/or their partner as soon as the booking window opens.

## 2. Requirements
*   **Users**: Multiple independent users, each with their own Altea credentials.
*   **Selection**: Bookings are based on Class Name, Date, Time, and User.
*   **Timing**: Booking window opens **1 week + 1 hour** before the class start time.
*   **Platform**: Python script executed via Cron on a Linux/macOS server.
*   **Notifications**:
    *   Each user receives notifications for their own bookings.
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

## 5. Configuration

### `users.yaml` (gitignored - contains credentials)

```yaml
users:
  ryan:
    altea_email: "ryan@example.com"
    altea_password: "..."
    notification_email: "ryan@example.com"
  
  katie:
    altea_email: "katie@example.com"
    altea_password: "..."
    notification_email: "katie@example.com"
```

### `.env` (gitignored - Mailgun config)

```bash
MAILGUN_DOMAIN=mg.yourdomain.com
MAILGUN_API_KEY=key-xxx
FROM_EMAIL=altea-booking@yourdomain.com
```

### `classes.yaml` (weekly schedule)

```yaml
classes:
  - day: Monday
    time: "4:30 PM"
    name: "LF3 Strong"
    user: ryan
  
  - day: Tuesday
    time: "6:00 AM"
    name: "Hot Yoga"
    user: katie
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

