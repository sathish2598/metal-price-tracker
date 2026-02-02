"""Notification module for Email and SMS alerts."""

import json
import requests
from datetime import datetime
from typing import Optional

from config import Config


class AlertState:
    """Manages alert state to prevent duplicate notifications."""
    
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> dict:
        """Load alert state from file."""
        try:
            with open(Config.STATE_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "gold": {"10": None, "20": None},
                "silver": {"10": None, "20": None}
            }
    
    def _save_state(self):
        """Save alert state to file."""
        with open(Config.STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def was_alert_sent(self, metal: str, threshold: int) -> bool:
        """Check if an alert was already sent for this threshold."""
        if metal not in self.state:
            self.state[metal] = {"10": None, "20": None}
        
        return self.state[metal].get(str(threshold)) is not None
    
    def mark_alert_sent(self, metal: str, threshold: int):
        """Mark that an alert was sent."""
        if metal not in self.state:
            self.state[metal] = {"10": None, "20": None}
        
        self.state[metal][str(threshold)] = datetime.now().isoformat()
        self._save_state()
    
    def reset_alerts(self, metal: Optional[str] = None):
        """Reset alert state (when price recovers or baseline changes)."""
        if metal:
            self.state[metal] = {"10": None, "20": None}
        else:
            self.state = {
                "gold": {"10": None, "20": None},
                "silver": {"10": None, "20": None}
            }
        self._save_state()


class EmailNotifier:
    """Send email notifications using Resend (free tier: 100 emails/day)."""
    
    def __init__(self):
        self.api_key = Config.RESEND_API_KEY
        self.from_email = Config.EMAIL_FROM
        self.to_email = Config.EMAIL_TO
    
    def send(self, subject: str, html_body: str) -> bool:
        """Send an email notification."""
        if not Config.is_email_configured():
            print("Email not configured. Skipping email notification.")
            return False
        
        try:
            import resend
            resend.api_key = self.api_key
            
            response = resend.Emails.send({
                "from": self.from_email,
                "to": [self.to_email],
                "subject": subject,
                "html": html_body
            })
            
            print(f"Email sent successfully: {response.get('id', 'Unknown ID')}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def send_price_alert(self, metal: str, threshold: int, summary: dict) -> bool:
        """Send a price drop alert email."""
        subject = f"🚨 {metal.upper()} Price Alert: {threshold}% Drop!"
        
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h1 style="margin: 0;">🪙 Metal Price Alert</h1>
            </div>
            
            <div style="padding: 20px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;">
                <h2 style="color: #e74c3c; margin-top: 0;">
                    ⚠️ {metal.upper()} has dropped {threshold}% from baseline!
                </h2>
                
                <table style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Product</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">{summary['product_name']}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Current Price (with 3% GST)</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #e74c3c; font-weight: bold;">
                            ₹{summary['current_price_with_gst']:.2f}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Current Price (without GST)</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">₹{summary['current_price_without_gst']:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Baseline Price</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">₹{summary['baseline_price']:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Drop</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd; color: #e74c3c;">
                            {summary['drop_percentage']:.2f}%
                        </td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Buy Price</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">₹{summary['buy_price']:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;"><strong>Sell Price</strong></td>
                        <td style="padding: 10px; border-bottom: 1px solid #ddd;">₹{summary['sell_price']:.2f}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px;"><strong>Last Updated</strong></td>
                        <td style="padding: 10px;">{summary['updated_at']}</td>
                    </tr>
                </table>
            </div>
            
            <div style="padding: 20px; text-align: center; color: #666; font-size: 12px;">
                <p>This is an automated alert from Metal Price Tracker</p>
                <p>Data source: <a href="https://auragold.netlify.app">Aura Gold</a></p>
            </div>
        </body>
        </html>
        """
        
        return self.send(subject, html_body)


class SMSNotifier:
    """Send SMS notifications using Fast2SMS (free tier for India) or Textbelt."""
    
    def __init__(self):
        self.textbelt_key = Config.TEXTBELT_KEY
        self.fast2sms_key = getattr(Config, 'FAST2SMS_API_KEY', '')
        self.phone_number = Config.PHONE_NUMBER
    
    def send(self, message: str) -> bool:
        """Send an SMS notification."""
        if not Config.is_sms_configured():
            print("SMS not configured. Skipping SMS notification.")
            return False
        
        # Check if it's an Indian number
        is_indian = self.phone_number.startswith("+91") or self.phone_number.startswith("91")
        
        if is_indian and self.fast2sms_key:
            return self._send_fast2sms(message)
        elif is_indian:
            # Try Fast2SMS first, then fallback info
            print("Indian number detected. Fast2SMS recommended for India.")
            print("Get free API key at: https://www.fast2sms.com/")
            return self._send_textbelt(message)  # Will likely fail but try anyway
        else:
            return self._send_textbelt(message)
    
    def _send_fast2sms(self, message: str) -> bool:
        """Send SMS via Fast2SMS (works for India, free tier available)."""
        try:
            # Remove +91 or 91 prefix for Fast2SMS
            phone = self.phone_number
            if phone.startswith("+91"):
                phone = phone[3:]
            elif phone.startswith("91"):
                phone = phone[2:]
            
            response = requests.post(
                "https://www.fast2sms.com/dev/bulkV2",
                headers={
                    "authorization": self.fast2sms_key,
                    "Content-Type": "application/json"
                },
                json={
                    "route": "q",  # Quick SMS route (free)
                    "message": message,
                    "language": "english",
                    "flash": 0,
                    "numbers": phone
                },
                timeout=30
            )
            
            result = response.json()
            
            if result.get("return"):
                print(f"SMS sent successfully via Fast2SMS")
                return True
            else:
                print(f"Fast2SMS failed: {result.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"Failed to send SMS via Fast2SMS: {e}")
            return False
    
    def _send_textbelt(self, message: str) -> bool:
        """Send SMS via Textbelt (international, but limited free tier)."""
        try:
            response = requests.post(
                "https://textbelt.com/text",
                data={
                    "phone": self.phone_number,
                    "message": message,
                    "key": self.textbelt_key
                },
                timeout=30
            )
            
            result = response.json()
            
            if result.get("success"):
                print(f"SMS sent successfully via Textbelt")
                return True
            else:
                error = result.get('error', 'Unknown error')
                print(f"SMS failed: {error}")
                if "country" in error.lower():
                    print("\n💡 For Indian numbers, use Fast2SMS (free):")
                    print("   1. Sign up at https://www.fast2sms.com/")
                    print("   2. Get your API key from Dev API section")
                    print("   3. Add to .env: FAST2SMS_API_KEY=your_key")
                return False
                
        except Exception as e:
            print(f"Failed to send SMS: {e}")
            return False
    
    def send_price_alert(self, metal: str, threshold: int, summary: dict) -> bool:
        """Send a price drop alert SMS."""
        message = (
            f"🚨 {metal.upper()} PRICE ALERT!\n"
            f"Price dropped {threshold}%!\n"
            f"Current: ₹{summary['current_price_with_gst']:.2f}\n"
            f"Baseline: ₹{summary['baseline_price']:.2f}\n"
            f"Drop: {summary['drop_percentage']:.2f}%"
        )
        
        return self.send(message)


class Notifier:
    """Combined notifier that handles both email and SMS."""
    
    def __init__(self):
        self.email = EmailNotifier()
        self.sms = SMSNotifier()
        self.alert_state = AlertState()
    
    def send_price_alert(self, metal: str, threshold: int, summary: dict) -> dict:
        """Send price alert via both channels if not already sent."""
        results = {"email": False, "sms": False, "skipped": False}
        
        # Check if alert was already sent
        if self.alert_state.was_alert_sent(metal, threshold):
            print(f"Alert for {metal} {threshold}% drop was already sent. Skipping.")
            results["skipped"] = True
            return results
        
        # Send email
        if Config.is_email_configured():
            results["email"] = self.email.send_price_alert(metal, threshold, summary)
        
        # Send SMS
        if Config.is_sms_configured():
            results["sms"] = self.sms.send_price_alert(metal, threshold, summary)
        
        # Mark alert as sent if any notification succeeded
        if results["email"] or results["sms"]:
            self.alert_state.mark_alert_sent(metal, threshold)
        
        return results
    
    def reset_alerts(self, metal: Optional[str] = None):
        """Reset alert state."""
        self.alert_state.reset_alerts(metal)
        print(f"Alert state reset for: {metal or 'all metals'}")


def main():
    """Test the notifier."""
    notifier = Notifier()
    
    # Test with sample data
    sample_summary = {
        "metal": "GOLD",
        "product_name": "Aura Digital Gold 24K",
        "current_price_with_gst": 12000.00,
        "current_price_without_gst": 11650.49,
        "buy_price": 11650.49,
        "sell_price": 11417.48,
        "baseline_price": 14000.00,
        "drop_percentage": 14.29,
        "updated_at": datetime.now().isoformat(),
        "gst_rate": "3%"
    }
    
    print("Testing notification system...")
    print(f"Email configured: {Config.is_email_configured()}")
    print(f"SMS configured: {Config.is_sms_configured()}")
    
    # Uncomment below to test actual sending
    # results = notifier.send_price_alert("gold", 10, sample_summary)
    # print(f"Results: {results}")


if __name__ == "__main__":
    main()
