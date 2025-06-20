import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

def fetch_price_data(symbol, interval, start_time, end_time):
    """
    Fetches price data from Binance API with a fallback to a proxy server.
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
        # Fallback to the primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data

def get_eth_price_change():
    """
    Determines if the ETH price went up or down at the specified time.
    """
    # Define the specific time and date
    target_date = datetime(2025, 6, 13, 16, 0, 0)  # June 13, 2025, 4 PM ET
    et_timezone = pytz.timezone('US/Eastern')
    target_date = et_timezone.localize(target_date)
    utc_date = target_date.astimezone(pytz.utc)

    # Convert to milliseconds for Binance API
    start_time = int(utc_date.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data
    data = fetch_price_data("ETHUSDT", "1h", start_time, end_time)

    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        price_change = close_price - open_price

        if price_change >= 0:
            return "p2"  # Up
        else:
            return "p1"  # Down
    else:
        return "p3"  # Unknown/50-50 due to no data

def main():
    result = get_eth_price_change()
    print(f"recommendation: {result}")

if __name__ == "__main__":
    main()