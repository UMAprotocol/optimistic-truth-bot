import requests
import logging
from datetime import datetime, timedelta, timezone
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)

def get_data(symbol, start_time, end_time, proxy_url, primary_url):
    """
    Fetches data from Binance API using a proxy and falls back to the primary endpoint if necessary.
    """
    try:
        # First try the proxy endpoint
        response = requests.get(f"{proxy_url}?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.warning(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(f"{primary_url}/klines?symbol={symbol}&interval=1m&limit=1&startTime={start_time}&endTime={end_time}", timeout=10)
        response.raise_for_status()
        return response.json()

def get_close_price(symbol, date_str, hour, minute, timezone_str, proxy_url, primary_url):
    """
    Fetches the close price for a specific minute candle on Binance.
    """
    tz = pytz.timezone(timezone_str)
    naive_datetime = datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S")
    local_datetime = tz.localize(naive_datetime)
    utc_datetime = local_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 60000  # 1 minute later

    data = get_data(symbol, start_time, end_time, proxy_url, primary_url)
    close_price = float(data[0][4])  # Close price is the 5th element in the list
    return close_price

def main():
    """
    Main function to determine if the price of HYPE/USDC went up or down between two specific dates and times.
    """
    symbol = "HYPEUSDC"
    date1 = "2025-05-23"
    date2 = "2025-05-24"
    hour = 12
    minute = 0
    timezone_str = "US/Eastern"
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3"

    try:
        price1 = get_close_price(symbol, date1, hour, minute, timezone_str, proxy_url, primary_url)
        price2 = get_close_price(symbol, date2, hour, minute, timezone_str, proxy_url, primary_url)

        if price1 < price2:
            recommendation = "p2"  # Up
        elif price1 > price2:
            recommendation = "p1"  # Down
        else:
            recommendation = "p3"  # 50-50

        print(f"recommendation: {recommendation}")
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()