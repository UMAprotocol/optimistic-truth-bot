import requests
import os
from dotenv import load_dotenv
import logging
from datetime import datetime, timedelta, timezone
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_binance_data(symbol, interval, start_time, end_time):
    """
    Fetches data from Binance API with a fallback to a proxy if the primary fails.
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
        response = requests.get(PROXY_BINANCE_API, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy.")
        return data
    except Exception as e:
        logging.warning(f"Proxy failed with error: {e}. Trying primary endpoint.")
        try:
            # Fallback to the primary endpoint if proxy fails
            response = requests.get(PRIMARY_BINANCE_API, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Primary endpoint also failed with error: {e}.")
            raise

def get_candle_data(symbol, date_str, hour):
    """
    Retrieves the closing price for a specific hour candle on a given date for the specified symbol.
    """
    # Convert date and hour to the correct timestamp
    date_time = datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    tz = pytz.timezone("America/New_York")  # Binance uses UTC, so we convert ET to UTC
    date_time_utc = tz.localize(date_time).astimezone(pytz.utc)
    
    start_time = int(date_time_utc.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # Add one hour in milliseconds
    
    # Fetch the candle data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    
    # Extract the closing price from the first candle
    if data and len(data) > 0:
        close_price = float(data[0][4])
        return close_price
    else:
        raise ValueError("No data returned for the specified time and symbol.")

def main():
    """
    Main function to determine if the Bitcoin price went up or down for the specified candle.
    """
    symbol = "BTCUSDT"
    date_str = "2025-05-31"
    hour = 1  # 1 AM ET
    
    try:
        # Get the closing price for the specified candle
        closing_price_start = get_candle_data(symbol, date_str, hour)
        closing_price_end = get_candle_data(symbol, date_str, hour + 1)
        
        # Determine if the price went up or down
        if closing_price_end >= closing_price_start:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        print("recommendation: p3")  # Unknown/50-50 if there's an error

if __name__ == "__main__":
    main()