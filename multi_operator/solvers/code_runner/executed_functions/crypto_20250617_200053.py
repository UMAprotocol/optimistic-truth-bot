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
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    primary_url = "https://api.binance.com/api/v3/klines"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market():
    """
    Resolves the market based on the Solana price movement on Binance.
    """
    symbol = "SOLUSDT"
    target_date = datetime(2025, 6, 17, 15, 0, 0, tzinfo=pytz.timezone("US/Eastern"))  # June 17, 2025, 3PM ET
    target_date_utc = target_date.astimezone(pytz.utc)
    start_time = int(target_date_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    try:
        data = get_data(symbol, start_time, end_time)
        if data:
            open_price = float(data[1])
            close_price = float(data[4])
            if close_price >= open_price:
                return "recommendation: p2"  # Up
            else:
                return "recommendation: p1"  # Down
    except Exception as e:
        logger.error(f"Error fetching or processing data: {e}")
        return "recommendation: p3"  # Unknown/50-50 if error occurs

def main():
    """
    Main function to execute the market resolution.
    """
    result = resolve_market()
    print(result)

if __name__ == "__main__":
    main()