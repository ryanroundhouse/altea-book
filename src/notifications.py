"""
Email notification service for Altea booking bot.
Sends booking success/failure notifications via Mailgun.
"""

import os
import requests
from datetime import datetime
from typing import Optional


class EmailNotifier:
    """Handles email notifications via Mailgun API."""
    
    def __init__(self):
        """Initialize with environment variables."""
        self.mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        self.mailgun_api_key = os.getenv('MAILGUN_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL')
        self.to_email = os.getenv('TO_EMAIL')
        self.wife_email = os.getenv('WIFE_EMAIL')
        
        if not all([self.mailgun_domain, self.mailgun_api_key, self.from_email, self.to_email]):
            raise ValueError(
                "Missing required environment variables. "
                "Please set MAILGUN_DOMAIN, MAILGUN_API_KEY, FROM_EMAIL, and TO_EMAIL in .env file."
            )
    
    def send_email(self, to_emails: list, subject: str, html_content: str):
        """
        Send email using Mailgun API.
        
        Args:
            to_emails: List of recipient email addresses
            subject: Email subject
            html_content: HTML email body
            
        Returns:
            Response from Mailgun API
        """
        url = f"https://api.mailgun.net/v3/{self.mailgun_domain}/messages"
        
        data = {
            "from": self.from_email,
            "to": to_emails,
            "subject": subject,
            "html": html_content
        }
        
        response = requests.post(
            url,
            auth=("api", self.mailgun_api_key),
            data=data
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to send email: {response.status_code} - {response.text}")
    
    def generate_success_email(self, class_info: dict, for_wife: bool = False) -> str:
        """
        Generate HTML for successful booking notification.
        
        Args:
            class_info: Dictionary with class details (title, time, date, url, spots_left)
            for_wife: Whether this booking was for wife
            
        Returns:
            HTML email content
        """
        recipient_name = "your wife" if for_wife else "you"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        .success-icon {{
            font-size: 64px;
            margin-bottom: 10px;
        }}
        .title {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .subtitle {{
            font-size: 18px;
            color: #666;
            margin-top: 5px;
        }}
        .class-card {{
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            border-left: 5px solid #667eea;
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
        }}
        .class-title {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(102, 126, 234, 0.2);
        }}
        .detail-label {{
            font-weight: bold;
            color: #667eea;
        }}
        .detail-value {{
            color: #333;
        }}
        .message {{
            text-align: center;
            font-size: 16px;
            color: #666;
            margin: 25px 0;
            line-height: 1.6;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #999;
            font-size: 14px;
        }}
        .timestamp {{
            font-size: 12px;
            color: #999;
            text-align: center;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="success-icon">✅</div>
            <h1 class="title">Booking Successful!</h1>
            <p class="subtitle">Class booked for {recipient_name}</p>
        </div>
        
        <div class="class-card">
            <div class="class-title">{class_info.get('title', 'Unknown Class')}</div>
            
            <div class="detail-row">
                <span class="detail-label">📅 Date:</span>
                <span class="detail-value">{class_info.get('date', 'N/A')}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">⏰ Time:</span>
                <span class="detail-value">{class_info.get('time', 'N/A')}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">👥 Spots Left:</span>
                <span class="detail-value">{class_info.get('spots_left', 'N/A')}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">🔗 Class URL:</span>
                <span class="detail-value">
                    <a href="https://myaltea.app{class_info.get('url', '')}" style="color: #667eea;">View Class</a>
                </span>
            </div>
        </div>
        
        <div class="message">
            🎉 Your spot has been successfully reserved!<br>
            See you at the gym!
        </div>
        
        <div class="footer">
            <p>This is an automated notification from your Altea Booking Bot</p>
            <div class="timestamp">Booked at {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}</div>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def generate_failure_email(self, class_info: dict, error_message: str, for_wife: bool = False) -> str:
        """
        Generate HTML for failed booking notification.
        
        Args:
            class_info: Dictionary with class details
            error_message: Description of what went wrong
            for_wife: Whether this booking was for wife
            
        Returns:
            HTML email content
        """
        recipient_name = "your wife" if for_wife else "you"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 3px solid #f5576c;
        }}
        .error-icon {{
            font-size: 64px;
            margin-bottom: 10px;
        }}
        .title {{
            font-size: 32px;
            font-weight: bold;
            color: #f5576c;
            margin: 10px 0;
        }}
        .subtitle {{
            font-size: 18px;
            color: #666;
            margin-top: 5px;
        }}
        .class-card {{
            background: linear-gradient(135deg, #fff5f5 0%, #ffe0e0 100%);
            border-left: 5px solid #f5576c;
            border-radius: 8px;
            padding: 25px;
            margin: 25px 0;
        }}
        .class-title {{
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-bottom: 15px;
        }}
        .detail-row {{
            display: flex;
            justify-content: space-between;
            margin: 10px 0;
            padding: 8px 0;
            border-bottom: 1px solid rgba(245, 87, 108, 0.2);
        }}
        .detail-label {{
            font-weight: bold;
            color: #f5576c;
        }}
        .detail-value {{
            color: #333;
        }}
        .error-box {{
            background-color: #fff5f5;
            border: 2px solid #f5576c;
            border-radius: 8px;
            padding: 20px;
            margin: 25px 0;
        }}
        .error-title {{
            font-weight: bold;
            color: #f5576c;
            margin-bottom: 10px;
            font-size: 16px;
        }}
        .error-message {{
            color: #666;
            line-height: 1.6;
        }}
        .message {{
            text-align: center;
            font-size: 16px;
            color: #666;
            margin: 25px 0;
            line-height: 1.6;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #999;
            font-size: 14px;
        }}
        .timestamp {{
            font-size: 12px;
            color: #999;
            text-align: center;
            margin-top: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="error-icon">❌</div>
            <h1 class="title">Booking Failed</h1>
            <p class="subtitle">Could not book class for {recipient_name}</p>
        </div>
        
        <div class="class-card">
            <div class="class-title">{class_info.get('title', 'Unknown Class')}</div>
            
            <div class="detail-row">
                <span class="detail-label">📅 Date:</span>
                <span class="detail-value">{class_info.get('date', 'N/A')}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">⏰ Time:</span>
                <span class="detail-value">{class_info.get('time', 'N/A')}</span>
            </div>
            
            <div class="detail-row">
                <span class="detail-label">👥 Spots Left:</span>
                <span class="detail-value">{class_info.get('spots_left', 'N/A')}</span>
            </div>
        </div>
        
        <div class="error-box">
            <div class="error-title">⚠️ Error Details:</div>
            <div class="error-message">{error_message}</div>
        </div>
        
        <div class="message">
            Please check the class availability and try booking manually if needed.
        </div>
        
        <div class="footer">
            <p>This is an automated notification from your Altea Booking Bot</p>
            <div class="timestamp">Attempted at {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}</div>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def send_booking_success(self, class_info: dict, for_wife: bool = False):
        """
        Send success notification email.
        
        Args:
            class_info: Dictionary with class details
            for_wife: Whether this booking was for wife
        """
        html = self.generate_success_email(class_info, for_wife)
        subject = f"✅ Booking Confirmed: {class_info.get('title', 'Class')} on {class_info.get('date', '')}"
        
        # Determine recipients
        recipients = [self.to_email]
        if for_wife and self.wife_email:
            recipients.append(self.wife_email)
        
        print(f"\n📧 Sending success notification to: {', '.join(recipients)}")
        
        try:
            response = self.send_email(recipients, subject, html)
            print(f"✓ Email sent successfully! Message ID: {response.get('id', 'N/A')}")
            return response
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            raise
    
    def send_booking_failure(self, class_info: dict, error_message: str, for_wife: bool = False):
        """
        Send failure notification email.
        
        Args:
            class_info: Dictionary with class details
            error_message: Description of what went wrong
            for_wife: Whether this booking was for wife
        """
        html = self.generate_failure_email(class_info, error_message, for_wife)
        subject = f"❌ Booking Failed: {class_info.get('title', 'Class')} on {class_info.get('date', '')}"
        
        # Determine recipients
        recipients = [self.to_email]
        if for_wife and self.wife_email:
            recipients.append(self.wife_email)
        
        print(f"\n📧 Sending failure notification to: {', '.join(recipients)}")
        
        try:
            response = self.send_email(recipients, subject, html)
            print(f"✓ Email sent successfully! Message ID: {response.get('id', 'N/A')}")
            return response
        except Exception as e:
            print(f"✗ Failed to send email: {e}")
            raise

