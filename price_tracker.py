"""Price tracking module for Gold and Silver."""

import json
import requests
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from config import Config


@dataclass
class PriceData:
    """Data class for metal price information."""
    metal: str
    product_name: str
    price_with_gst: float
    price_without_gst: float
    buy_price: float
    sell_price: float
    updated_at: str
    
    @property
    def display_price(self) -> float:
        """Return the price with GST for display."""
        return self.price_with_gst


class PriceTracker:
    """Tracks metal prices from Aura Gold API."""
    
    def __init__(self):
        self.baseline_prices = self._load_baseline_prices()
    
    def _load_baseline_prices(self) -> dict:
        """Load baseline prices from file."""
        try:
            with open(Config.BASELINE_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"gold": None, "silver": None, "set_at": None}
    
    def _save_baseline_prices(self):
        """Save baseline prices to file."""
        with open(Config.BASELINE_FILE, 'w') as f:
            json.dump(self.baseline_prices, f, indent=2)
    
    def set_baseline(self, metal: str, price: float):
        """Set baseline price for a metal."""
        self.baseline_prices[metal] = price
        self.baseline_prices["set_at"] = datetime.now().isoformat()
        self._save_baseline_prices()
        print(f"Baseline set for {metal}: ₹{price:.2f}")
    
    def get_baseline(self, metal: str) -> Optional[float]:
        """Get baseline price for a metal."""
        # Check environment variable first
        if metal == "gold" and Config.GOLD_BASELINE_PRICE > 0:
            return Config.GOLD_BASELINE_PRICE
        if metal == "silver" and Config.SILVER_BASELINE_PRICE > 0:
            return Config.SILVER_BASELINE_PRICE
        
        return self.baseline_prices.get(metal)
    
    def fetch_current_price(self, metal: str) -> Optional[PriceData]:
        """Fetch current price for gold or silver."""
        url = Config.GOLD_API_URL if metal == "gold" else Config.SILVER_API_URL
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("success") or not data.get("data"):
                print(f"API returned unsuccessful response for {metal}")
                return None
            
            # Get the latest price (last item in the array)
            latest = data["data"][-1]
            
            return PriceData(
                metal=metal,
                product_name=latest["product_name"],
                price_with_gst=latest["price_with_gst"],
                price_without_gst=latest["price_without_gst"],
                buy_price=latest["aura_buy_price"],
                sell_price=latest["aura_sell_price"],
                updated_at=latest["updated_at"]
            )
            
        except requests.RequestException as e:
            print(f"Error fetching {metal} price: {e}")
            return None
        except (KeyError, IndexError) as e:
            print(f"Error parsing {metal} price data: {e}")
            return None
    
    def calculate_drop_percentage(self, metal: str, current_price: float) -> Optional[float]:
        """Calculate percentage drop from baseline."""
        baseline = self.get_baseline(metal)
        if baseline is None or baseline <= 0:
            return None
        
        drop = ((baseline - current_price) / baseline) * 100
        return drop
    
    def check_alerts(self, metal: str, current_price: float) -> list:
        """Check if any alert thresholds are met.
        
        Returns list of triggered alert levels (e.g., [10, 20])
        """
        drop_percentage = self.calculate_drop_percentage(metal, current_price)
        
        if drop_percentage is None:
            return []
        
        alerts = []
        
        if Config.ALERT_10_PERCENT and drop_percentage >= 10:
            alerts.append(10)
        
        if Config.ALERT_20_PERCENT and drop_percentage >= 20:
            alerts.append(20)
        
        return alerts
    
    def get_price_summary(self, price_data: PriceData) -> dict:
        """Get a summary of price with baseline comparison."""
        baseline = self.get_baseline(price_data.metal)
        drop_percentage = self.calculate_drop_percentage(price_data.metal, price_data.display_price)
        
        return {
            "metal": price_data.metal.upper(),
            "product_name": price_data.product_name,
            "current_price_with_gst": price_data.price_with_gst,
            "current_price_without_gst": price_data.price_without_gst,
            "buy_price": price_data.buy_price,
            "sell_price": price_data.sell_price,
            "baseline_price": baseline,
            "drop_percentage": drop_percentage,
            "updated_at": price_data.updated_at,
            "gst_rate": "3%"
        }


def main():
    """Test the price tracker."""
    tracker = PriceTracker()
    
    print("Fetching current prices...\n")
    
    for metal in ["gold", "silver"]:
        price_data = tracker.fetch_current_price(metal)
        if price_data:
            summary = tracker.get_price_summary(price_data)
            print(f"=== {summary['metal']} ===")
            print(f"Product: {summary['product_name']}")
            print(f"Price (with 3% GST): ₹{summary['current_price_with_gst']:.2f}")
            print(f"Price (without GST): ₹{summary['current_price_without_gst']:.2f}")
            print(f"Buy Price: ₹{summary['buy_price']:.2f}")
            print(f"Sell Price: ₹{summary['sell_price']:.2f}")
            
            if summary['baseline_price']:
                print(f"Baseline: ₹{summary['baseline_price']:.2f}")
                if summary['drop_percentage'] is not None:
                    direction = "down" if summary['drop_percentage'] > 0 else "up"
                    print(f"Change: {abs(summary['drop_percentage']):.2f}% {direction}")
            else:
                print("Baseline: Not set")
            
            print(f"Updated: {summary['updated_at']}")
            print()


if __name__ == "__main__":
    main()
