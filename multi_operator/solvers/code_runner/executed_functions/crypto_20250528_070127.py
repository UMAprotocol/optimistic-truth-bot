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

# Binance API URLs
PRIMARY_BINANCE_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_BINANCE_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_binance_data(symbol, interval, start_time, end_time):
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
        # Try fetching data from the proxy endpoint first
        response = requests.get(PROXY_BINANCE_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        logging.info("Data fetched successfully from proxy endpoint.")
        return data
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}. Falling back to primary endpoint.")
        # If proxy fails, fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_BINANCE_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            logging.info("Data fetched successfully from primary endpoint.")
            return data
        except Exception as e:
            logging.error(f"Both proxy and primary endpoint failed: {e}")
            raise

def get_candle_data_for_specific_time(symbol, date_str, hour):
    """
    Get the closing price of a specific 1-hour candle for the given symbol on Binance.
    """
    # Convert local time to UTC
    local_time = datetime.strptime(f"{date_str} {hour}:00:00", "%Y-%m-%d %H:%M:%S")
    local_time = pytz.timezone("America/New_York").localize(local_time)
    utc_time = local_time.astimezone(pytz.utc)
    
    # Convert datetime to milliseconds since epoch
    start_time = int(utc_time.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later in milliseconds
    
    # Fetch candle data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    
    # Extract the closing price from the first candle
    if data and len(data) > 0:
        close_price = float(data[0][4])
        return close_price
    else:
        logging.error("No data available for the specified time and symbol.")
        return None

def resolve_market():
    """
    Resolve the market based on the change in price for the BTC/USDT pair on Binance.
    """
    symbol = "BTCUSDT"
    date_str = "2025-05-28"
    hour = 2  # 2 AM ET
    
    try:
        # Get closing price for the specified hour
        closing_price = get_candle_data_for_specific_time(symbol, date_str, hour)
        if closing_price is not None:
            # Compare closing price to the opening price to determine market resolution
            opening_price = get_candle_data_for_specific_time(symbol, date_str, hour - 1)
            if opening_price is not None and closing_price >= opening_price:
                print("recommendation: p2")  # Up
            else:
                print("recommendation: p1")  # Down
        else:
            print("recommendation: p3")  # Unknown/50-50 if no data available
    except Exception as e:
        logging.error(f"Error resolving market: {e}")
        print("recommendation: p3")  # Unknown/50-50 in case of error

if __name__ == "__main__":
    resolve_market()