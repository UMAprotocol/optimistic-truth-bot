import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary request fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Both API requests failed: {e}")
            raise

def get_price_change(symbol, target_datetime):
    """
    Determines the price change for a given cryptocurrency symbol at a specific datetime.
    """
    # Convert datetime to the correct format for the API call
    utc_time = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_time.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 60000  # One minute later

    # Fetch the data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = (close_price - open_price) / open_price * 100
        return price_change
    else:
        logging.error("No data available for the specified time.")
        return None

def main():
    """
    Main function to determine if the price of BTC/USDT went up or down at the specified time.
    """
    target_datetime = datetime(2025, 6, 13, 1, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    
    try:
        price_change = get_price_change(symbol, target_datetime)
        if price_change is not None:
            if price_change >= 0:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 due to error

if __name__ == "__main__":
    main()