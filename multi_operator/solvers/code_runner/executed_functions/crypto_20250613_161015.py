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
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")
        # Fall back to primary endpoint if proxy fails
        response = requests.get(PRIMARY_API_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0]

def resolve_market(symbol, target_datetime):
    """
    Resolves the market based on the price change of the specified symbol at the given datetime.
    """
    # Convert target datetime to UTC timestamp in milliseconds
    utc_datetime = target_datetime.astimezone(pytz.utc)
    start_time = int(utc_datetime.timestamp() * 1000)
    end_time = start_time + 3600000  # 1 hour later

    # Fetch price data for the start and end of the interval
    start_data = fetch_price_data(symbol, "1h", start_time, start_time + 60000)  # 1 minute after start
    end_data = fetch_price_data(symbol, "1h", end_time, end_time + 60000)  # 1 minute after end

    if start_data and end_data:
        start_price = float(start_data[1])  # Open price
        end_price = float(end_data[4])  # Close price

        # Determine if the price went up or down
        if end_price >= start_price:
            return "recommendation: p2"  # Up
        else:
            return "recommendation: p1"  # Down
    else:
        return "recommendation: p3"  # Unknown/50-50

def main():
    # Example usage
    target_datetime = datetime(2025, 6, 13, 11, 0, tzinfo=pytz.timezone("US/Eastern"))
    symbol = "ETHUSDT"
    result = resolve_market(symbol, target_datetime)
    print(result)

if __name__ == "__main__":
    main()