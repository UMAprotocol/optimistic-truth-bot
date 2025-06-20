import requests
import os
from datetime import datetime, timedelta
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
        # Try fetching data using the proxy API first
        response = requests.get(PROXY_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data
    except Exception as e:
        print(f"Proxy API request failed: {e}, falling back to primary API")
        try:
            # Fallback to the primary API if proxy fails
            response = requests.get(PRIMARY_API_URL, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            if data:
                return data
        except Exception as e:
            print(f"Primary API request failed: {e}")
            return None

def resolve_market(symbol, target_date_str, target_hour):
    """
    Resolves the market based on the opening and closing prices of the specified symbol at the given date and time.
    """
    # Convert date string to datetime object
    target_date = datetime.strptime(target_date_str, "%Y-%m-%d")
    # Calculate start and end timestamps in milliseconds
    start_time = int(datetime.timestamp(target_date.replace(hour=target_hour)) * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch data
    data = fetch_binance_data(symbol, "1h", start_time, end_time)
    if data:
        open_price = float(data[0][1])
        close_price = float(data[0][4])
        if close_price >= open_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    result = resolve_market("BTCUSDT", "2025-06-19", 9)  # June 19, 2025, 9 AM ET
    print(result)

if __name__ == "__main__":
    main()