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
        "startTime": start_time,
        "endTime": end_time,
        "limit": 1
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
            logging.error(f"Primary API failed: {e}.")
            raise

def get_candle_data_for_specific_time(symbol, target_datetime):
    """
    Retrieves the closing price of a specific 1-hour candle for the given datetime.
    """
    # Convert datetime to the correct format for the API call
    start_time = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Add one hour in milliseconds

    # Fetch the candle data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)
    
    # Extract the closing price from the first candle returned
    if data and len(data) > 0:
        close_price = float(data[0][4])
        return close_price
    else:
        logging.error("No data returned for the specified time.")
        return None

def main():
    # Define the target date and time
    target_datetime_str = "2025-06-12 18:00:00"
    target_timezone = "US/Eastern"
    symbol = "BTCUSDT"

    # Convert string to datetime object
    target_datetime = datetime.strptime(target_datetime_str, "%Y-%m-%d %H:%M:%S")
    target_datetime = pytz.timezone(target_timezone).localize(target_datetime)

    # Convert to UTC
    target_datetime_utc = target_datetime.astimezone(pytz.utc)

    # Get the closing price of the 1-hour candle starting at the target time
    try:
        close_price = get_candle_data_for_specific_time(symbol, target_datetime_utc)
        if close_price is not None:
            logging.info(f"Closing price for {symbol} at {target_datetime_str} is {close_price}")
            print(f"Closing price: {close_price}")
        else:
            print("recommendation: p4")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p4")

if __name__ == "__main__":
    main()