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
PRIMARY_API_URL = "https://api.binance.com/api/v3"
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
        response = requests.get(f"{PROXY_API_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        try:
            response = requests.get(f"{PRIMARY_API_URL}/klines", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0]
        except Exception as e:
            print(f"Primary endpoint also failed: {str(e)}")
            return None

def get_eth_price_change():
    """
    Determines the price change of ETH/USDT for the 1-hour candle starting at 12 PM ET on June 14, 2025.
    """
    # Define the time for the query
    target_date = datetime(2025, 6, 14, 12, 0, 0, tzinfo=pytz.timezone("US/Eastern"))
    start_time = int(target_date.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 3600000  # 1 hour later in milliseconds

    # Fetch the candle data
    candle_data = fetch_price_data("ETHUSDT", "1h", start_time, end_time)
    if candle_data:
        open_price = float(candle_data[1])
        close_price = float(candle_data[4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on the price change
        if price_change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 due to data fetch failure

def main():
    resolution = get_eth_price_change()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()