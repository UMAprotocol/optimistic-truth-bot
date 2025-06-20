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
        return data
    except Exception as e:
        print(f"Proxy endpoint failed: {e}, falling back to primary endpoint")
        # Fallback to the primary endpoint
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def get_eth_price_change():
    """
    Determines the price change of ETH/USDT for the 1-hour candle starting at 3 PM ET on June 14, 2025.
    """
    # Define the time for the event
    event_time_str = "2025-06-14 15:00:00"
    event_time = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
    event_time = pytz.timezone("US/Eastern").localize(event_time)
    event_time_utc = event_time.astimezone(pytz.utc)

    # Convert to milliseconds for Binance API
    start_time = int(event_time_utc.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch the price data
    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time)

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change_percentage = ((close_price - open_price) / open_price) * 100

        # Determine the resolution based on the price change
        if price_change_percentage >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 if no data available

def main():
    resolution = get_eth_price_change()
    print(f"recommendation: {resolution}")

if __name__ == "__main__":
    main()