import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_price(symbol, date_str, time_str, timezone_str):
    """
    Fetch the closing price of a cryptocurrency from Binance at a specified date and time.
    """
    # Convert local time to UTC timestamp
    local_tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
    local_datetime = local_tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Parameters for API request
    params = {
        'symbol': symbol,
        'interval': '1m',
        'startTime': timestamp,
        'endTime': timestamp + 60000,  # 1 minute range
        'limit': 1
    }

    # Try fetching from proxy first
    try:
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element in the list
        return close_price
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary API.")

    # Fallback to primary API if proxy fails
    try:
        response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price
    except Exception as e:
        logging.error(f"Primary API failed with error: {e}")
        raise

def main():
    # Define the symbol and times for comparison
    symbol = "ETHUSDT"
    date1 = "2025-04-14"
    time1 = "12:00"
    date2 = "2025-04-15"
    time2 = "12:00"
    timezone_str = "US/Eastern"

    try:
        # Fetch prices
        price1 = fetch_price(symbol, date1, time1, timezone_str)
        price2 = fetch_price(symbol, date2, time2, timezone_str)

        # Determine the resolution based on prices
        if price1 < price2:
            recommendation = "p2"  # Up
        elif price1 > price2:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50

        print(f"recommendation: {recommendation}")
    except Exception as e:
        logging.error(f"Failed to fetch prices or determine resolution: {e}")
        print("recommendation: p4")  # Unknown or error

if __name__ == "__main__":
    main()