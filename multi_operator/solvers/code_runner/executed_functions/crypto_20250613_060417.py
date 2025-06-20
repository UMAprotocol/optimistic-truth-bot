import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance using the proxy endpoint with a fallback to the primary endpoint.
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 1,
        "startTime": start_time,
        "endTime": end_time
    }
    
    try:
        # Try fetching data from the proxy endpoint
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        try:
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {e}")
            return None

def get_eth_price_change():
    """
    Determines the price change of ETH/USDT for the 1-hour candle starting at June 13, 1 AM ET.
    """
    # Define the time and symbol details
    symbol = "ETHUSDT"
    interval = "1h"
    timezone = pytz.timezone("US/Eastern")
    start_time = timezone.localize(datetime(2025, 6, 13, 1, 0, 0)).astimezone(pytz.utc)
    end_time = start_time + timedelta(hours=1)

    # Convert datetime to milliseconds for the API call
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = int(end_time.timestamp() * 1000)

    # Fetch the price data
    data = fetch_price_data(symbol, interval, start_time_ms, end_time_ms)
    if data:
        open_price = float(data[1])
        close_price = float(data[4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on the price change
        if price_change_percentage >= 0:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50 due to data fetch failure

def main():
    result = get_eth_price_change()
    print(result)

if __name__ == "__main__":
    main()