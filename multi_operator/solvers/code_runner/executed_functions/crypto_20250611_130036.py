import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API = "https://api.binance.com/api/v3"
PROXY_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy API with a fallback to the primary API.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy API
        response = requests.get(f"{PROXY_API}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        # Fallback to the primary API
        response = requests.get(f"{PRIMARY_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from primary API.")
        return data

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    target_timestamp = int(target_datetime.timestamp() * 1000)
    
    # Fetch price data for the target hour
    data = fetch_price_data(symbol, "1h", target_timestamp, target_timestamp + 3600000)
    
    if not data:
        logging.error("No data returned from API.")
        return "recommendation: p3"  # Unknown/50-50 if no data
    
    # Extract the opening and closing prices from the data
    open_price = float(data[0][1])
    close_price = float(data[0][4])
    
    # Determine if the price went up or down
    if close_price >= open_price:
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Define the symbol and the target datetime
    symbol = "ETHUSDT"
    target_datetime = datetime(2025, 6, 11, 8, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    # Resolve the market
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()