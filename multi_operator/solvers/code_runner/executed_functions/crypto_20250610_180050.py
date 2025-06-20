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
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}?symbol={symbol}&interval={interval}&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def resolve_market():
    """
    Resolves the market based on the change in BTC/USDT price from Binance.
    """
    # Define the time for the 1 hour candle on June 10, 1 PM ET
    target_time = datetime(2025, 6, 10, 13, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    start_time = int(target_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the data
    data = get_binance_data("BTCUSDT", "1h", start_time, end_time)

    # Extract the opening and closing prices
    open_price = float(data[0][1])
    close_price = float(data[0][4])

    # Determine the resolution based on price change
    if close_price >= open_price:
        recommendation = "p2"  # Up
    else:
        recommendation = "p1"  # Down

    return recommendation

def main():
    """
    Main function to execute the market resolution.
    """
    try:
        result = resolve_market()
        print(f"recommendation: {result}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()