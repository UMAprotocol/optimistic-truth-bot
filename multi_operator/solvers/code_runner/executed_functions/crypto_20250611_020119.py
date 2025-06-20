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
PRIMARY_API_ENDPOINT = "https://api.binance.com/api/v3"
PROXY_API_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_data_from_binance(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy endpoint if the primary fails.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching from proxy endpoint first
        response = requests.get(f"{PROXY_API_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        try:
            # Fallback to primary endpoint
            response = requests.get(f"{PRIMARY_API_ENDPOINT}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both endpoints failed: {e}")
            raise

def get_price_change(symbol, target_datetime):
    """
    Calculates the price change for the specified symbol at the given datetime.
    """
    # Convert datetime to the correct format for the API call
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_data_from_binance(symbol, "1h", start_time, end_time)
    
    if data and len(data) > 0:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100
        return price_change_percentage
    else:
        logging.error("No data available for the specified time.")
        return None

def main():
    """
    Main function to determine if the Bitcoin price went up or down.
    """
    target_datetime = datetime(2025, 6, 10, 21, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "BTCUSDT"
    
    try:
        price_change_percentage = get_price_change(symbol, target_datetime)
        if price_change_percentage is not None:
            if price_change_percentage >= 0:
                print("recommendation: p1")  # Price went up or stayed the same
            else:
                print("recommendation: p2")  # Price went down
        else:
            print("recommendation: p3")  # Unknown or data not available
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Default to unknown in case of error

if __name__ == "__main__":
    main()