import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import logging

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy server if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data using the proxy endpoint
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy API.")
        return data
    except Exception as e:
        logging.warning(f"Proxy API failed: {e}. Attempting primary API.")
        try:
            # Fallback to the primary API endpoint
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary API.")
            return data
        except Exception as e:
            logging.error(f"Primary API also failed: {e}")
            raise

def get_candle_data(symbol, date, hour):
    """
    Retrieves the closing price of a specific hourly candle for the given symbol on Binance.
    """
    # Convert local time to UTC
    et_timezone = pytz.timezone('US/Eastern')
    local_dt = et_timezone.localize(datetime(date.year, date.month, date.day, hour, 0, 0))
    utc_dt = local_dt.astimezone(pytz.utc)
    
    # Calculate start and end times in milliseconds
    start_time = int(utc_dt.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later
    
    # Fetch the candle data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        close_price = float(data[0][4])  # Closing price is the fifth element
        return close_price
    else:
        raise ValueError("No data returned for the specified time and symbol.")

def main():
    """
    Main function to determine if the Bitcoin price went up or down for the specified candle.
    """
    try:
        # Specific date and time for the candle
        date = datetime(2025, 5, 28)
        hour = 9  # 9 AM ET
        
        # Get the closing price for the specified candle
        close_price_start = get_candle_data("BTCUSDT", date, hour)
        close_price_end = get_candle_data("BTCUSDT", date, hour + 1)
        
        # Determine if the price went up or down
        if close_price_end >= close_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()