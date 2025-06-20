import requests
import os
from datetime import datetime
from dotenv import load_dotenv
import pytz

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_URL = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_URL = "https://api.binance.com/api/v3"

def get_data(symbol, start_time):
    """
    Fetches the open and close price for a specific 1-hour candle on Binance.
    """
    # Convert the start time to milliseconds
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Try the proxy endpoint first
    try:
        response = requests.get(
            f"{PROXY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1h",
                "startTime": start_time_ms,
                "endTime": end_time_ms,
                "limit": 1
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][1], data[0][4]  # Open and Close prices
    except Exception as e:
        print(f"Proxy endpoint failed: {str(e)}, falling back to primary endpoint")

    # Fall back to primary endpoint if proxy fails
    try:
        response = requests.get(
            f"{PRIMARY_URL}/klines",
            params={
                "symbol": symbol,
                "interval": "1h",
                "startTime": start_time_ms,
                "endTime": end_time_ms,
                "limit": 1
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        if data:
            return data[0][1], data[0][4]  # Open and Close prices
    except Exception as e:
        print(f"Primary endpoint also failed: {str(e)}")
        return None, None

def resolve_market(symbol, event_time):
    """
    Determines the market resolution based on the open and close prices.
    """
    open_price, close_price = get_data(symbol, event_time)
    if open_price is None or close_price is None:
        return "recommendation: p4"  # Unable to resolve

    if float(close_price) >= float(open_price):
        return "recommendation: p2"  # Up
    else:
        return "recommendation: p1"  # Down

def main():
    # Define the event time and symbol
    event_time = datetime(2025, 6, 19, 4, 0, 0, tzinfo=pytz.timezone('US/Eastern'))
    symbol = "SOLUSDT"

    # Resolve the market based on the event time and symbol
    result = resolve_market(symbol, event_time)
    print(result)

if __name__ == "__main__":
    main()