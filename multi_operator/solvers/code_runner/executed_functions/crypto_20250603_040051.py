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
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_data(symbol, start_time, end_time):
    primary_url = "https://api.binance.com/api/v3"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return float(data[0][4])  # Close price

def resolve_market():
    # Define the specific date and time for the market resolution
    target_date = datetime(2025, 6, 2, 23, 0, 0, tzinfo=pytz.timezone('US/Eastern'))  # June 2, 2025, 11 PM ET
    start_time = int(target_date.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Plus one hour

    # Symbol for the market
    symbol = "BTCUSDT"

    # Fetch the closing price at the specified time
    try:
        close_price_start = get_data(symbol, start_time, start_time + 60000)  # Start of the hour
        close_price_end = get_data(symbol, end_time, end_time + 60000)  # End of the hour

        if close_price_end >= close_price_start:
            return "recommendation: p2"  # Market resolves to "Up"
        else:
            return "recommendation: p1"  # Market resolves to "Down"
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        return "recommendation: p3"  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    result = resolve_market()
    print(result)