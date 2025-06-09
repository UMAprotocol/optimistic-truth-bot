import requests
import os
from datetime import datetime, timezone
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
    
    try:
        # Try fetching data using the proxy API first
        response = requests.get(PROXY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][4]  # Close price
    except Exception as e:
        print(f"Proxy API failed: {e}, falling back to primary API")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data[0][4]  # Close price
        except Exception as e:
            print(f"Primary API failed: {e}")
            return None

def main():
    # Specific date and time for the query
    target_datetime = datetime(2025, 6, 9, 8, 0, tzinfo=timezone.utc)
    start_time = int(target_datetime.timestamp() * 1000)  # Convert to milliseconds
    end_time = start_time + 60000  # 1 minute later

    # Fetch the close price of BTCUSDT at the specified time
    close_price = fetch_binance_data("BTCUSDT", "1m", start_time, end_time)

    # Determine the resolution based on the close price
    if close_price is None:
        print("recommendation: p4")  # Unable to fetch data
    elif float(close_price) >= 225000:
        print("recommendation: p2")  # Yes, price is higher than or equal to 225,000 USDT
    else:
        print("recommendation: p1")  # No, price is lower than 225,000 USDT

if __name__ == "__main__":
    main()