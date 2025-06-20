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

def fetch_eth_price_data(date_str, hour, minute, timezone_str):
    """
    Fetches the ETH/USDT price data from Binance for a specific hour candle on a given date.
    
    Args:
        date_str (str): Date in YYYY-MM-DD format.
        hour (int): Hour of the day (24-hour format).
        minute (int): Minute of the hour.
        timezone_str (str): Timezone string.
    
    Returns:
        tuple: Open and close prices of the ETH/USDT pair.
    """
    # Convert local time to UTC
    tz = pytz.timezone(timezone_str)
    local_dt = tz.localize(datetime.strptime(f"{date_str} {hour}:{minute}:00", "%Y-%m-%d %H:%M:%S"))
    utc_dt = local_dt.astimezone(pytz.utc)
    start_time = int(utc_dt.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # URLs for Binance API
    proxy_url = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
    primary_url = "https://api.binance.com/api/v3/klines"

    # Parameters for API request
    params = {
        "symbol": "ETHUSDT",
        "interval": "1h",
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }

    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(proxy_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            open_price = float(data[0][1])
            close_price = float(data[0][4])
            return open_price, close_price
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(primary_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                open_price = float(data[0][1])
                close_price = float(data[0][4])
                return open_price, close_price
        except Exception as e:
            logging.error(f"Both endpoints failed: {e}")
            raise

def main():
    """
    Main function to determine if the ETH price went up or down.
    """
    # Specific date and time for the query
    date_str = "2025-06-18"
    hour = 2  # 2 AM ET
    minute = 0
    timezone_str = "US/Eastern"

    try:
        open_price, close_price = fetch_eth_price_data(date_str, hour, minute, timezone_str)
        logging.info(f"Open price: {open_price}, Close price: {close_price}")

        if close_price >= open_price:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logging.error(f"Error fetching price data: {e}")
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()