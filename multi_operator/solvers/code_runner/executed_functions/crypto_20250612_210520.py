import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    try:
        # Try proxy endpoint first
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_time):
    """
    Resolves the market based on the price change of the symbol at the specified target time.
    """
    # Convert target time to UTC milliseconds
    target_time_utc = int(target_time.timestamp() * 1000)
    data = get_binance_data(symbol, "1h", target_time_utc, target_time_utc + 3600000)  # 1 hour in milliseconds

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        change_percentage = ((close_price - open_price) / open_price) * 100

        if change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50

def main():
    """
    Main function to handle the resolution of the Bitcoin Up or Down market.
    """
    # Define the target time for the market resolution
    target_time_str = "2025-06-12 16:00:00"
    target_timezone = pytz.timezone("US/Eastern")
    target_time = target_timezone.localize(datetime.strptime(target_time_str, "%Y-%m-%d %H:%M:%S"))

    # Symbol for the market
    symbol = "BTCUSDT"

    # Resolve the market
    resolution = resolve_market(symbol, target_time)
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()