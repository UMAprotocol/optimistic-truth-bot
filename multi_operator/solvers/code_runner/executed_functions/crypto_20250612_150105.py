import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
PROXY_ENDPOINT = "https://minimal-ubuntu-production.up.railway.app/binance-proxy"
PRIMARY_ENDPOINT = "https://api.binance.com/api/v3"

def fetch_price_from_binance(symbol, start_time):
    """
    Fetches the closing price of a cryptocurrency from Binance for a specific 1-hour candle.
    
    Args:
        symbol (str): The symbol to fetch, e.g., 'ETHUSDT'.
        start_time (datetime): The start time of the 1-hour candle.
    
    Returns:
        float: The closing price of the cryptocurrency.
    """
    # Convert datetime to milliseconds since epoch
    start_time_ms = int(start_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1 hour later

    # Prepare the query parameters
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 1
    }

    # Try fetching from the proxy endpoint first
    try:
        response = requests.get(f"{PROXY_ENDPOINT}/api/v3/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Proxy failed with error: {e}. Trying primary endpoint.")

    # Fallback to the primary endpoint if proxy fails
    try:
        response = requests.get(f"{PRIMARY_ENDPOINT}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return float(data[0][4])  # Closing price
    except Exception as e:
        print(f"Primary endpoint failed with error: {e}.")
        raise

def main():
    # Define the event time and symbol
    event_time = datetime(2025, 6, 12, 10, 0)  # June 12, 2025, 10:00 AM ET
    symbol = "ETHUSDT"

    # Fetch the closing price for the specified time
    try:
        closing_price = fetch_price_from_binance(symbol, event_time)
        print(f"Closing price for {symbol} at {event_time} is {closing_price}")
        # Determine the resolution based on the closing price
        if closing_price >= 0:
            print("recommendation: p2")  # Up
        else:
            print("recommendation: p1")  # Down
    except Exception as e:
        print(f"Failed to fetch price data: {e}")
        print("recommendation: p3")  # Unknown/50-50 if data fetch fails

if __name__ == "__main__":
    main()