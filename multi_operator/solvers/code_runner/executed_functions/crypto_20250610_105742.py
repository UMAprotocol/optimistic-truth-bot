import requests
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API keys loaded from environment variables
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")

# API endpoints
PRIMARY_API_URL = "https://api.binance.com/api/v3/klines"
PROXY_API_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"

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
    headers = {
        "X-MBX-APIKEY": BINANCE_API_KEY
    }

    try:
        # Try fetching data using the proxy URL first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price
    except Exception as e:
        print(f"Proxy failed with error: {e}, trying primary API endpoint.")
        # Fallback to the primary API endpoint if proxy fails
        try:
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price
        except Exception as e:
            print(f"Primary API also failed with error: {e}")
            return None

def main():
    # Specific date and time for the query
    target_date = "2025-06-09"
    target_time = "09:00:00"
    target_datetime = datetime.strptime(f"{target_date} {target_time}", "%Y-%m-%d %H:%M:%S")
    target_timestamp = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds

    # Fetch the close price of BTCUSDT at the specified time
    close_price = fetch_binance_data("BTCUSDT", "1m", target_timestamp, target_timestamp + 60000)

    # Determine the resolution based on the close price
    if close_price is not None:
        close_price = float(close_price)
        if close_price >= 225000:
            print("recommendation: p2")  # Yes
        else:
            print("recommendation: p1")  # No
    else:
        print("recommendation: p4")  # Unable to resolve

if __name__ == "__main__":
    main()