# Google Calendar Integration Setup

This guide walks you through setting up automatic Google Calendar integration for your booked classes. Each user deploys their own Google Apps Script (takes ~5 minutes), and booked classes will automatically appear on their calendar.

## Overview

When you successfully book a class, the system sends the booking details to a Google Apps Script you deploy. The script then creates a calendar event in your Google Calendar. No Google Cloud project or complex OAuth setup required.

## Setup Instructions

### Step 1: Create a New Google Apps Script

1. Go to [script.google.com](https://script.google.com)
2. Click **New project**
3. Name it something like "Altea Calendar Integration"

### Step 2: Add the Script Code

Delete any existing code and paste the following:

```javascript
/**
 * Altea Calendar Integration
 * 
 * This script receives booking data from the Altea auto-booker
 * and creates calendar events in your Google Calendar.
 */

function doPost(e) {
  try {
    // Parse the incoming JSON data
    const data = JSON.parse(e.postData.contents);
    
    // Extract event details
    const title = data.title || 'Fitness Class';
    const startTime = new Date(data.startTime);
    const endTime = new Date(data.endTime);
    const description = data.description || '';
    const location = data.location || 'Altea Active';
    
    // Create the calendar event
    const calendar = CalendarApp.getDefaultCalendar();
    const event = calendar.createEvent(title, startTime, endTime, {
      description: description,
      location: location
    });
    
    // Return success response
    return ContentService
      .createTextOutput(JSON.stringify({ 
        success: true, 
        eventId: event.getId(),
        message: 'Event created successfully'
      }))
      .setMimeType(ContentService.MimeType.JSON);
      
  } catch (error) {
    // Return error response
    return ContentService
      .createTextOutput(JSON.stringify({ 
        success: false, 
        error: error.toString() 
      }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// Test function - run this manually to verify calendar access
function testCalendarAccess() {
  const calendar = CalendarApp.getDefaultCalendar();
  Logger.log('Calendar name: ' + calendar.getName());
  Logger.log('Calendar access verified!');
}
```

### Step 3: Deploy as Web App

1. Click **Deploy** > **New deployment**
2. Click the gear icon next to "Select type" and choose **Web app**
3. Configure:
   - **Description**: "Altea Calendar Integration v1"
   - **Execute as**: "Me" (your Google account)
   - **Who has access**: "Anyone"
4. Click **Deploy**
5. **Important**: Click **Authorize access** and grant the required permissions
6. Copy the **Web app URL** - it looks like:
   ```
   https://script.google.com/macros/s/AKfycb...xyz/exec
   ```

### Step 4: Add the URL to Your Configuration

Edit your `users.yaml` file and add the `calendar_webhook_url` for your user:

```yaml
users:
  ryan:
    altea_email: ryan@example.com
    altea_password: your-password
    notification_email: ryan@example.com
    calendar_webhook_url: https://script.google.com/macros/s/AKfycb...xyz/exec
```

That's it! Booked classes will now automatically appear in your Google Calendar.

## Testing Your Setup

You can test the integration without booking a class:

```bash
curl -X POST "YOUR_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "🏋️ Test Class",
    "startTime": "2025-12-15T10:00:00",
    "endTime": "2025-12-15T11:00:00",
    "description": "Test event from Altea booker",
    "location": "Altea Active"
  }'
```

You should see a new event in your Google Calendar.

## Troubleshooting

### "Authorization required" error
- Go back to your Apps Script project
- Run the `testCalendarAccess` function manually (click ▶️)
- Grant any requested permissions
- Re-deploy the web app

### Events not appearing
1. Check the Apps Script execution logs:
   - In Apps Script, click **Executions** in the left sidebar
   - Look for any error messages
2. Verify your webhook URL is correct in `users.yaml`
3. Make sure you deployed as a Web App (not just saved)

### Wrong calendar
By default, events are created in your primary Google Calendar. To use a different calendar, modify the script:

```javascript
// Replace this line:
const calendar = CalendarApp.getDefaultCalendar();

// With this (using calendar ID from calendar settings):
const calendar = CalendarApp.getCalendarById('your-calendar-id@group.calendar.google.com');
```

## Updating the Script

If you need to update the Apps Script code:

1. Make your changes in the script editor
2. Click **Deploy** > **Manage deployments**
3. Click the pencil icon to edit
4. Change **Version** to "New version"
5. Click **Deploy**

The webhook URL stays the same, so you don't need to update `users.yaml`.

## Security Notes

- The webhook URL is a secret - treat it like a password
- Anyone with the URL can create events in your calendar
- The script only has permission to manage your calendar (not read emails, etc.)
- You can delete the Apps Script project at any time to revoke access

