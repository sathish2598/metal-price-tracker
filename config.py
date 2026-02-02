"""Configuration management for Metal Price Tracker."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # API Endpoints
    GOLD_API_URL = "https://auragold.netlify.app/api/prices?metal=gold"
    SILVER_API_URL = "https://auragold.netlify.app/api/prices?metal=silver"
    
    # Email Configuration (Resend - Free tier: 100 emails/day)
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
    EMAIL_TO = os.getenv("EMAIL_TO", "")
    EMAIL_FROM = os.getenv("EMAIL_FROM", "Metal Price Tracker <onboarding@resend.dev>")
    
    # SMS Configuration
    # Textbelt - International (limited free tier)
    TEXTBELT_KEY = os.getenv("TEXTBELT_KEY", "textbelt")
    # Fast2SMS - India (free tier available)
    FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")
    PHONE_NUMBER = os.getenv("PHONE_NUMBER", "")
    
    # Alert Thresholds
    ALERT_10_PERCENT = os.getenv("ALERT_10_PERCENT", "true").lower() == "true"
    ALERT_20_PERCENT = os.getenv("ALERT_20_PERCENT", "true").lower() == "true"
    
    # Baseline Prices (for tracking price drops)
    GOLD_BASELINE_PRICE = float(os.getenv("GOLD_BASELINE_PRICE") or 0)
    SILVER_BASELINE_PRICE = float(os.getenv("SILVER_BASELINE_PRICE") or 0)
    
    # Check Interval
    CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
    
    # State file for tracking alerts sent
    STATE_FILE = os.path.join(os.path.dirname(__file__), "alert_state.json")
    BASELINE_FILE = os.path.join(os.path.dirname(__file__), "baseline_prices.json")
    
    @classmethod
    def is_email_configured(cls) -> bool:
        """Check if email is properly configured."""
        return bool(cls.RESEND_API_KEY and cls.EMAIL_TO)
    
    @classmethod
    def is_sms_configured(cls) -> bool:
        """Check if SMS is properly configured."""
        return bool(cls.PHONE_NUMBER)
