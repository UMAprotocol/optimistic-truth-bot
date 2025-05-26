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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants for API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price(symbol, date_str, timezone_str='US/Eastern'):
    """
    Fetch the closing price of a cryptocurrency at a specific time from Binance API.
    """
    # Convert date string to the correct timestamp
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(date_str, "%Y-%m-%d %H:%M")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    timestamp = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds

    params = {
        'symbol': symbol,
        'interval': '1m',
        'limit': 1,
        'startTime': timestamp,
        'endTime': timestamp + 60000  # 1 minute later
    }

    try:
        # Try fetching from the proxy API first
        response = requests.get(PROXY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    except Exception as e:
        logging.warning(f"Proxy API failed, trying primary API: {e}")
        # Fallback to the primary API if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
        close_price = float(data[0][4])
        return close_price

def main():
    # Define the symbols and times based on the specific market question
    symbol = "HYPEUSDC"
    date1 = "2025-05-22 12:00"
    date2 = "2025-05-23 12:00"

    try:
        # Fetch prices for both dates
        price1 = fetch_price(symbol, date1)
        price2 = fetch_price(symbol, date2)

        # Determine the market resolution based on the prices
        if price1 < price2:
            resolution = "p2"  # Up
        elif price1 > price2:
            resolution = "p1"  # Down
        else:
            resolution = "p3"  # 50-50

        print(f"recommendation: {resolution}")
    except Exception as e:
        logging.error(f"Error fetching prices: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()