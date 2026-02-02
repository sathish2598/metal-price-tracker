#!/usr/bin/env python3
"""
Metal Price Tracker - Main Entry Point

Monitors gold and silver prices from Aura Gold API and sends
notifications when prices drop by 10% or 20% from baseline.

SIP-Style Alerts: After each alert, the baseline automatically updates
to the current price, allowing you to receive alerts for every 10%/20%
drop (useful for buying in stages as prices fall).

Usage:
    python main.py              # Run once and check prices
    python main.py --daemon     # Run continuously with scheduled checks
    python main.py --set-baseline  # Set current prices as baseline
    python main.py --reset-alerts  # Reset alert state
    python main.py --status     # Show current status
"""

import argparse
import sys
import time
from datetime import datetime

from config import Config
from price_tracker import PriceTracker
from notifier import Notifier


def print_header():
    """Print application header."""
    print("\n" + "=" * 50)
    print("  🪙 Metal Price Tracker")
    print("  Data Source: Aura Gold (auragold.netlify.app)")
    print("=" * 50 + "\n")


def check_prices_and_notify(tracker: PriceTracker, notifier: Notifier):
    """Check prices and send notifications if thresholds are met."""
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking prices...")
    
    for metal in ["gold", "silver"]:
        price_data = tracker.fetch_current_price(metal)
        
        if not price_data:
            print(f"  ⚠️  Could not fetch {metal} price")
            continue
        
        summary = tracker.get_price_summary(price_data)
        
        # Display current status
        print(f"\n  📊 {summary['metal']}:")
        print(f"     Current Price: ₹{summary['current_price_with_gst']:.2f} (with 3% GST)")
        
        if summary['baseline_price']:
            print(f"     Baseline: ₹{summary['baseline_price']:.2f}")
            if summary['drop_percentage'] is not None:
                direction = "📉" if summary['drop_percentage'] > 0 else "📈"
                color_word = "down" if summary['drop_percentage'] > 0 else "up"
                print(f"     Change: {direction} {abs(summary['drop_percentage']):.2f}% {color_word}")
        else:
            print(f"     ⚠️  Baseline not set. Run with --set-baseline to set it.")
            continue
        
        # Check for alerts
        alerts = tracker.check_alerts(metal, price_data.display_price)
        
        for threshold in alerts:
            print(f"\n  🚨 ALERT: {metal.upper()} has dropped {threshold}% from baseline!")
            
            results = notifier.send_price_alert(metal, threshold, summary)
            
            if results["skipped"]:
                print(f"     (Alert was already sent previously)")
            else:
                if results["email"]:
                    print(f"     ✅ Email notification sent")
                if results["sms"]:
                    print(f"     ✅ SMS notification sent")
                if not results["email"] and not results["sms"]:
                    print(f"     ⚠️  No notifications sent (check configuration)")
                
                # SIP-style: Auto-update baseline after alert is sent
                # This allows receiving alerts for the next 10%/20% drop
                if results["email"] or results["sms"]:
                    old_baseline = summary['baseline_price']
                    new_baseline = price_data.display_price
                    tracker.set_baseline(metal, new_baseline)
                    notifier.reset_alerts(metal)
                    print(f"     📊 Baseline updated: ₹{old_baseline:.2f} → ₹{new_baseline:.2f}")
                    print(f"     🔄 Ready for next {threshold}% drop alert")


def set_baseline(tracker: PriceTracker, notifier: Notifier):
    """Set current prices as baseline."""
    print("\nSetting current prices as baseline...")
    
    for metal in ["gold", "silver"]:
        price_data = tracker.fetch_current_price(metal)
        
        if price_data:
            tracker.set_baseline(metal, price_data.display_price)
            print(f"  ✅ {metal.upper()}: ₹{price_data.display_price:.2f}")
        else:
            print(f"  ⚠️  Could not fetch {metal} price")
    
    # Reset alerts when baseline changes
    notifier.reset_alerts()
    print("\n  Alert state has been reset.")


def show_status(tracker: PriceTracker):
    """Show current status and configuration."""
    print("\n📋 Configuration Status:")
    print(f"  Email configured: {'✅' if Config.is_email_configured() else '❌'}")
    print(f"  SMS configured: {'✅' if Config.is_sms_configured() else '❌'}")
    print(f"  Check interval: {Config.CHECK_INTERVAL_MINUTES} minutes")
    print(f"  10% alert: {'✅' if Config.ALERT_10_PERCENT else '❌'}")
    print(f"  20% alert: {'✅' if Config.ALERT_20_PERCENT else '❌'}")
    
    print("\n📊 Baseline Prices:")
    for metal in ["gold", "silver"]:
        baseline = tracker.get_baseline(metal)
        if baseline:
            print(f"  {metal.upper()}: ₹{baseline:.2f}")
        else:
            print(f"  {metal.upper()}: Not set")
    
    print("\n💰 Current Prices:")
    for metal in ["gold", "silver"]:
        price_data = tracker.fetch_current_price(metal)
        if price_data:
            summary = tracker.get_price_summary(price_data)
            print(f"\n  {summary['metal']}:")
            print(f"    Price (with GST): ₹{summary['current_price_with_gst']:.2f}")
            print(f"    Price (without GST): ₹{summary['current_price_without_gst']:.2f}")
            print(f"    Buy Price: ₹{summary['buy_price']:.2f}")
            print(f"    Sell Price: ₹{summary['sell_price']:.2f}")
            if summary['drop_percentage'] is not None:
                print(f"    Change from baseline: {summary['drop_percentage']:.2f}%")


def run_daemon(tracker: PriceTracker, notifier: Notifier):
    """Run continuously with scheduled checks."""
    import schedule
    
    print(f"\n🔄 Starting daemon mode...")
    print(f"   Checking every {Config.CHECK_INTERVAL_MINUTES} minutes")
    print(f"   Press Ctrl+C to stop\n")
    
    # Run immediately on start
    check_prices_and_notify(tracker, notifier)
    
    # Schedule periodic checks
    schedule.every(Config.CHECK_INTERVAL_MINUTES).minutes.do(
        check_prices_and_notify, tracker, notifier
    )
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute if scheduled task is due
    except KeyboardInterrupt:
        print("\n\n👋 Daemon stopped.")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Metal Price Tracker - Monitor gold and silver prices"
    )
    parser.add_argument(
        "--daemon", "-d",
        action="store_true",
        help="Run continuously with scheduled checks"
    )
    parser.add_argument(
        "--set-baseline", "-b",
        action="store_true",
        help="Set current prices as baseline"
    )
    parser.add_argument(
        "--reset-alerts", "-r",
        action="store_true",
        help="Reset alert state"
    )
    parser.add_argument(
        "--status", "-s",
        action="store_true",
        help="Show current status"
    )
    
    args = parser.parse_args()
    
    print_header()
    
    tracker = PriceTracker()
    notifier = Notifier()
    
    if args.set_baseline:
        set_baseline(tracker, notifier)
    elif args.reset_alerts:
        notifier.reset_alerts()
        print("✅ Alert state has been reset.")
    elif args.status:
        show_status(tracker)
    elif args.daemon:
        run_daemon(tracker, notifier)
    else:
        # Default: run once
        check_prices_and_notify(tracker, notifier)
    
    print("")


if __name__ == "__main__":
    main()
