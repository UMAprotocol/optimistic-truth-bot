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
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def get_data(symbol, start_time, end_time):
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"
    
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1h&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market(symbol, target_datetime):
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_datetime.replace(tzinfo=timezone.utc).timestamp() * 1000)
    
    # Fetch data for the specific hour
    data = get_data(symbol, target_timestamp, target_timestamp + 3600000)  # 1 hour in milliseconds
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data

def main():
    # Example: Solana Up or Down - June 17, 3PM ET
    symbol = "SOLUSDT"
    target_datetime = datetime(2025, 6, 17, 15, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    try:
        result = resolve_market(symbol, target_datetime)
        print(f"recommendation: {result}")
    except Exception as e:
        logger.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Default to unknown/50-50 in case of error

if __name__ == "__main__":
    main()