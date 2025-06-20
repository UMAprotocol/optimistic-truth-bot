import requests
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_eth_price_change(date_str, hour=0, minute=0, timezone_str="US/Eastern"):
    """
    Fetches the percentage change for the ETHUSDT pair on Binance for a specific 1-hour candle.

    Args:
        date_str: Date in YYYY-MM-DD format
        hour: Hour in 24-hour format (default: 0 for 12AM)
        minute: Minute (default: 0)
        timezone_str: Timezone string (default: "US/Eastern")

    Returns:
        Percentage change as float or None if data cannot be fetched.
    """
    # Convert the target time to UTC timestamp
    tz = pytz.timezone(timezone_str)
    target_time_local = tz.localize(datetime.strptime(f"{date_str} {hour:02d}:{minute:02d}:00", "%Y-%m-%d %H:%M:%S"))
    target_time_utc = target_time_local.astimezone(timezone.utc)
    start_time_ms = int(target_time_utc.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # URLs setup
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Try proxy endpoint first
    try:
        response = requests.get(f"{proxy_url}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time_ms}&endTime={end_time_ms}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return 100 * (close_price - open_price) / open_price
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")

    # Fallback to primary endpoint
    try:
        response = requests.get(f"{primary_url}?symbol=ETHUSDT&interval=1h&limit=1&startTime={start_time_ms}&endTime={end_time_ms}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return 100 * (close_price - open_price) / open_price
    except Exception as e:
        logging.error(f"Primary endpoint also failed: {str(e)}")
        return None

def main():
    """
    Main function to determine if the ETH price went up or down on June 11, 12AM ET.
    """
    date_str = "2025-06-11"  # Specific date for the query
    change = get_eth_price_change(date_str)
    if change is not None:
        if change >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    else:
        print("recommendation: p3")  # Unknown/50-50 due to data fetch failure

if __name__ == "__main__":
    main()