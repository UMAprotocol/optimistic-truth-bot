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

# Binance API endpoints
PRIMARY_BINANCE_API = "https://api.binance.com/api/v3"
PROXY_BINANCE_API = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        # Try fetching data from the proxy endpoint first
        response = requests.get(f"{PROXY_BINANCE_API}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        logging.warning(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_BINANCE_API}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            logging.error(f"Primary endpoint also failed: {e}")
            raise

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the symbol at the specified datetime.
    """
    # Convert datetime to the appropriate timestamp for the API
    start_timestamp = int(target_datetime.timestamp() * 1000)
    end_timestamp = start_timestamp + 3600000  # 1 hour later

    # Fetch the data for the specified time
    data = fetch_binance_data(symbol, "1h", start_timestamp, end_timestamp)
    
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on the price change
        if price_change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data is available

def main():
    """
    Main function to handle the resolution of the Ethereum market.
    """
    # Define the target datetime for the market resolution
    target_datetime = datetime(2025, 6, 11, 6, 0, tzinfo=pytz.timezone("US/Eastern"))
    
    # Symbol for the market
    symbol = "ETHUSDT"
    
    try:
        resolution = resolve_market(symbol, target_datetime)
        print(f"recommendation: {resolution}")
    except Exception as e:
        logging.error(f"Failed to resolve market: {e}")
        print("recommendation: p3")  # Default to unknown if there's an error

if __name__ == "__main__":
    main()